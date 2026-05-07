import { createBffServer } from "./app/createBffServer.js";
import { loadConfig } from "./config/index.js";

const config = loadConfig();
const { httpServer, io } = createBffServer({ config });

httpServer.listen(config.port, config.host, () => {
  console.log(
    `bff-notifications listening on ${config.host}:${config.port}`,
  );
});

function shutdown() {
  io.close(() => {
    if (!httpServer.listening) {
      process.exit(0);
      return;
    }

    httpServer.close(() => process.exit(0));
  });
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
