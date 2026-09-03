import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    ALPACA_API_KEY: process.env.ALPACA_API_KEY,
    ALPACA_SECRET_KEY: process.env.ALPACA_SECRET_KEY,
    ACCOUNT_ID: "PA3LL11TFH7L",
    ETHERSCAN_TX: "0x46f3ce0bdb9e343a4d2c85b57146a5c2fca5c5dd861c9aadab00f21bb75f396d",
  },
};

export default nextConfig;
