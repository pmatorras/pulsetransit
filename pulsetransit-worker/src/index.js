export default {
	// Manual trigger for debugging
	async fetch(req, env, ctx) {
		if (new URL(req.url).pathname === "/trigger") {
			await collectEstimaciones(env);  // await directly, don't use waitUntil
			return new Response("Triggered manually");
		}
		return new Response("pulsetransit-estimaciones worker running");
	},

	async scheduled(event, env, ctx) {
		if (event.cron === "0 * * * *") {
			await collectPosiciones(env);
		} else {
			await collectEstimaciones(env);
		}
	},
};

async function collectEstimaciones(env) {
	const url = "https://datos.santander.es/api/rest/datasets/control_flotas_estimaciones.json?rows=5000";
	const resp = await fetch(url, { signal: AbortSignal.timeout(25000) });
	if (!resp.ok) throw new Error(`API fetch failed: ${resp.status}`);

	const json = await resp.json();
	const rows = json.resources ?? [];
	const collectedAt = new Date().toISOString();

	let inserted = 0;
	for (const item of rows) {
		const fechActual = item["ayto:fechActual"] ?? null;
		const tiempo1 = item["ayto:tiempo1"] ?? null;

		let predictedArrival = null;
		if (fechActual && tiempo1 !== null) {
			try {
				const t = new Date(fechActual);
				t.setSeconds(t.getSeconds() + Number(tiempo1));
				predictedArrival = t.toISOString();
			} catch (_) { }
		}

		const result = await env.DB.prepare(`
      INSERT OR IGNORE INTO estimaciones
        (collected_at, parada_id, linea, fech_actual, tiempo1, tiempo2,
         distancia1, distancia2, destino1, destino2, predicted_arrival)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
			collectedAt,
			item["ayto:paradaId"] ?? null,
			item["ayto:etiqLinea"] ?? null,
			fechActual,
			tiempo1,
			item["ayto:tiempo2"] ?? null,
			item["ayto:distancia1"] ?? null,
			item["ayto:distancia2"] ?? null,
			item["ayto:destino1"] ?? null,
			item["ayto:destino2"] ?? null,
			predictedArrival,
		).run();

		if (result.meta.changes > 0) inserted++;
	}

	console.log(`[${collectedAt}] estimaciones: ${inserted} new rows from ${rows.length} fetched`);
}
