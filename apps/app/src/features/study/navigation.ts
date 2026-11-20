import { router } from "expo-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { isLimit, limitRoute } from "../commerce/navigation";
import { startPractice, type TopicStart } from "./api";

export type Origin = "lessons" | "today" | "notebook" | "photo";
export function origin(value?: string): Origin {
  return value === "today" || value === "notebook" || value === "photo"
    ? value
    : "lessons";
}
export function leave(from: Origin) {
  router.dismissTo(`/${from}`);
}
export function useStartPractice(from: Origin, replace = false) {
  const cache = useQueryClient();
  return useMutation({
    mutationFn: (data: TopicStart) => startPractice(data),
    networkMode: "always",
    onError: (error) => {
      if (isLimit(error)) router.push(limitRoute(error, from));
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
