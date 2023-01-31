import babel from "@rollup/plugin-babel";
import external from "rollup-plugin-peer-deps-external";
import resolve from "rollup-plugin-node-resolve";
import commonjs from "rollup-plugin-commonjs";
import replace from "rollup-plugin-replace";

export default {
  input: "./src/index.js",
  output: {
    file: "./lib/dev.js",
    format: "cjs"
  },
  plugins: [
    external(),
    babel({
      exclude: "node_modules/**",
      babelHelpers: "bundled"
    }),
    resolve(),
    commonjs()
  ]
};
