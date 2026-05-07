export type LoadState = "idle" | "loading" | "success" | "error";

export interface LoadStateProps {
  state: LoadState;
}
