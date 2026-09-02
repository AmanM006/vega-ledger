import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  env: {
    ALPACA_API_KEY: process.env.ALPACA_API_KEY,
    ALPACA_SECRET_KEY: process.env.ALPACA_SECRET_KEY,
    ACCOUNT_ID: "PA3D4EOEK0PA",
    ETHERSCAN_TX: "0x711b6ea9f659a094a8c929c5f6fdd707ccb6c50de2e8c3d3e76515df94d64daf",
  },
};

export default nextConfig;
