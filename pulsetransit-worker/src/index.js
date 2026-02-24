export default {
	async fetch(req, env, ctx) {
		const url = new URL(req.url);
		
		if (url.pathname === "/trigger") {
			await collectEstimaciones(env);
			await new Promise(r => setTimeout(r, 1000));
			await collectPosiciones(env);
			return new Response("Triggered estimaciones+posiciones");
		}
		
		if (url.pathname === "/health") {
			const lastEst = await env.DB.prepare(
				"SELECT MAX(collected_at) as last FROM estimaciones"
			).first();
			const lastPos = await env.DB.prepare(
				"SELECT MAX(collected_at) as last FROM posiciones"
			).first();
			
			return Response.json({
				status: "ok",
				last_estimaciones: lastEst?.last,
				last_posiciones: lastPos?.last
			});
		}
		
		return new Response("pulsetransit-worker running");
	},

	async scheduled(event, env, ctx) {
		if (event.cron === "0 * * * *") {
			await collectPosiciones(env);
		} else if (event.cron === "*/2 * * * *") {
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

async function collectPosiciones(env) {
  const url = "https://datos.santander.es/api/rest/datasets/control_flotas_posiciones.json?rows=5000";
  const resp = await fetch(url, { signal: AbortSignal.timeout(25000) });
  if (!resp.ok) throw new Error(`API fetch failed: ${resp.status}`);

  const json = await resp.json();
  const rows = json.resources ?? [];
  const collectedAt = new Date().toISOString();

  let inserted = 0;
  for (const item of rows) {
    const result = await env.DB.prepare(`
      INSERT OR IGNORE INTO posiciones
        (collected_at, instante, vehiculo, linea, lat, lon, velocidad, estado)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      collectedAt,
      item["ayto:instante"]       ?? null,
      item["ayto:vehiculo"]       ?? null,
      item["ayto:linea"]          ?? null,
      item["wgs84_pos:lat"]       ?? null,
      item["wgs84_pos:long"]      ?? null,
      item["ayto:velocidad"]      ?? null,
      item["ayto:estado"]         ?? null,
    ).run();

    if (result.meta.changes > 0) inserted++;
  }

  console.log(`[${collectedAt}] posiciones: ${inserted} new rows from ${rows.length} fetched`);
}
