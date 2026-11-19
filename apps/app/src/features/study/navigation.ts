import { router } from "expo-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { startPractice, type TopicStart } from "./api";

export type Origin = "lessons" | "today";
export function origin(value?: string): Origin {
  return value === "today" ? "today" : "lessons";
}
export function leave(from: Origin) {
  router.dismissTo(from === "today" ? "/today" : "/lessons");
}
export function useStartPractice(from: Origin, replace = false) {
  const cache = useQueryClient();
  return useMutation({
    mutationFn: (data: TopicStart) => startPractice(data),
    networkMode: "always",
    onSuccess: (session) => {
      cache.setQueryData(["practice", session.id], session);
      const destination = {
        pathname: "/practice/[sessionId]" as const,
        params: { sessionId: session.id, from },
      };
      if (replace) router.replace(destination);
      else router.push(destination);
    },
  });
}
