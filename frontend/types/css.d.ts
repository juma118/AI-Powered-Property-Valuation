// Next's built-in types only declare ambient modules for CSS Modules
// (*.module.css). Plain stylesheet side-effect imports (e.g. leaflet's own
// CSS) have no type declaration otherwise, which newer TypeScript versions
// flag as ts(2882) "Cannot find module or type declarations for side-effect
// import".
declare module '*.css';
