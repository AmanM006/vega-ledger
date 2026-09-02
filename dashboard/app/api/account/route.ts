import { NextResponse } from "next/server";

const BASE = "https://paper-api.alpaca.markets/v2";

function alpacaHeaders() {
  return {
    "APCA-API-KEY-ID": process.env.ALPACA_API_KEY || "",
    "APCA-API-SECRET-KEY": process.env.ALPACA_SECRET_KEY || "",
    "Content-Type": "application/json",
  };
}

export async function GET() {
  try {
    const [accountRes, positionsRes, ordersRes] = await Promise.all([
      fetch(`${BASE}/account`, { headers: alpacaHeaders(), cache: "no-store" }),
      fetch(`${BASE}/positions`, { headers: alpacaHeaders(), cache: "no-store" }),
      fetch(`${BASE}/orders?status=all&limit=10`, { headers: alpacaHeaders(), cache: "no-store" }),
    ]);

    const [account, positions, orders] = await Promise.all([
      accountRes.json(),
      positionsRes.json(),
      ordersRes.json(),
    ]);

    return NextResponse.json({ account, positions, orders });
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 500 });
  }
}
