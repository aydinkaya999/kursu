import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { AppState } from "react-native";
import { getConfig, getMe } from "./api";

export const meKey = ["me"] as const;
export function useMe() {
  return useQuery({
    queryKey: meKey,
    queryFn: getMe,
    retry: false,
    networkMode: "always",
  });
}
export function useConfig() {
  const query = useQuery({
    queryKey: ["config"],
    queryFn: getConfig,
    retry: false,
    networkMode: "always",
    refetchInterval: (q) =>
      q.state.data ? q.state.data.seconds_to_midnight * 1000 : false,
  });
  const { refetch } = query;
  useEffect(() => {
    const sub = AppState.addEventListener("change", (s) => {
      if (s === "active") void refetch();
    });
    return () => sub.remove();
  }, [refetch]);
  return query;
}
