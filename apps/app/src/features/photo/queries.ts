import { useQuery } from "@tanstack/react-query";
import { useFocusEffect } from "expo-router";
import { useCallback } from "react";
import { getPhotoQuota } from "./api";

export function usePhotoQuota(
  owner: string | undefined,
  configUpdatedAt: number,
) {
  const query = useQuery({
    queryKey: ["photo-quota", owner],
    queryFn: getPhotoQuota,
    enabled: !!owner,
    retry: false,
  });
  const { refetch } = query;
  useFocusEffect(
    useCallback(() => {
      if (owner && configUpdatedAt) void refetch();
    }, [owner, configUpdatedAt, refetch]),
  );
  return query;
}
