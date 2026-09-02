import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET() {
  try {
    const logPath = path.join(process.cwd(), "..", "data", "verifiable_log.json");
    if (!fs.existsSync(logPath)) {
      return NextResponse.json({ entries: [], error: "Log not found" });
    }
    const raw = fs.readFileSync(logPath, "utf-8");
    const chain = JSON.parse(raw);
    // Return last 20 entries, newest first
    const entries = chain.slice(-20).reverse();
    return NextResponse.json({ entries, total: chain.length });
  } catch (e) {
    return NextResponse.json({ entries: [], error: String(e) }, { status: 500 });
  }
}
