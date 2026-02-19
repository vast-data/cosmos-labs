const PROXY_CONFIG = {
  "/users": {
    "target": "http://agent.v151",
    "secure": false,
    "changeOrigin": true,
    "logLevel": "debug", // info debug warn error silent
    "headers": {'Access-Control-Allow-Origin': '*'}
  },
  "/token": {
    "target": "http://agent.v151",
    "secure": false,
    "changeOrigin": true,
    "logLevel": "debug", // info debug warn error silent
    "headers": {'Access-Control-Allow-Origin': '*'}
  },
  "/api/v1": {
    "target": "http://agent.v151",
    "secure": false,
    "changeOrigin": true,
    "logLevel": "debug", // info debug warn error silent
    "headers": {'Access-Control-Allow-Origin': '*'}
  },
};

console.log(`Proxy to: http://agent.v151 \n`)
module.exports = PROXY_CONFIG;
