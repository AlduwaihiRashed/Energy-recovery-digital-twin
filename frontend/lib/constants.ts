// Mirrors backend/app/config.py and backend/app/sim/physics.py. Duplicated
// rather than fetched because these are fixed constants, not data -- avoids
// a round trip for every chart render.
export const ROW_INTERVAL_HOURS = (1.0 * 240.0 * 3) / 3600.0; // SIM_TICK_INTERVAL_S * SIM_TIME_SCALE * DB_PERSIST_EVERY_N_TICKS / 3600
export const REVENUE_PER_KWH = 0.075;
export const CO2_KG_PER_KWH = 0.45;
