import { Redirect } from "expo-router";
import { useMe } from "../src/features/placement/queries";
import { StatusScreen } from "../src/features/placement/Status";
export default function Index() {
  const me = useMe();
  if (!me.data)
    return <StatusScreen error={me.error} retry={() => void me.refetch()} />;
  return <Redirect href={me.data.profile ? "/today" : "/onboarding"} />;
}
