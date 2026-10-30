import { readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
const directory = new URL("../src/receipttrace/static/", import.meta.url);
for (const name of readdirSync(directory).filter((name) => name.endsWith(".js"))) {
  const result = spawnSync(process.execPath, ["--check", fileURLToPath(new URL(name, directory))], {
    stdio: "inherit",
  });
  if (result.status !== 0) process.exit(result.status ?? 1);
}
console.log("Frontend JavaScript syntax checked.");
