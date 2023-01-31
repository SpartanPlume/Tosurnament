export default {
  server: {
    port: 3001
  },
  env: {
    OSU_CLIENT_ID: process.env.OSU_CLIENT_ID,
    OSU_REDIRECT_URI: process.env.OSU_REDIRECT_URI,
    PRIVATE_TOSURNAMENT_API_PATH: process.env.PRIVATE_TOSURNAMENT_API_PATH
  }
};
