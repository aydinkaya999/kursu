import { Button, Label, Screen } from "../../components/Core";
import { tr } from "../../i18n/tr";
import { RequestFailure } from "../../lib/session";
import { Status } from "../placement/Status";
export function StudyStatus({
  error,
  retry,
  onBack,
}: {
  error?: unknown;
  retry: () => void;
  onBack: () => void;
}) {
  return (
    <Screen>
      {error instanceof RequestFailure &&
      (error.status === 404 || error.status === 409) ? (
        <>
          <Label>{tr.study.unavailable}</Label>
          <Button label={tr.health.retry} onPress={retry} />
        </>
      ) : (
        <Status error={error} retry={retry} />
      )}
      <Button variant="text" label={tr.nav.back} onPress={onBack} />
    </Screen>
  );
}
