declare module "canvas-confetti" {
  type Options = Record<string, unknown>;
  const confetti: (options?: Options) => Promise<null> | null;
  export default confetti;
}
