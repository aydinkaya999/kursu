import { router } from "expo-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { RequestFailure } from "../../lib/session";
import { startPractice, type TopicStart } from "./api";

export type Origin = "lessons" | "today" | "notebook";
export function origin(value?: string): Origin {
  return value === "today" || value === "notebook" ? value : "lessons";
}
export function leave(from: Origin) {
  router.dismissTo(`/${from}`);
}
export function useStartPractice(from: Origin, replace = false) {
  const cache = useQueryClient();
  return useMutation({
    mutationFn: (data: TopicStart) => startPractice(data),
    networkMode: "always",
    onError: (error, data) => {
      if (
        data.kind === "review" &&
        error instanceof RequestFailure &&
        error.status === 403
      )
        router.push({ pathname: "/paywall", params: { from } });
    },
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
