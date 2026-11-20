import { Platform } from "react-native";
import { client } from "../../lib/api";
import { authorized, requireSuccess } from "../../lib/session";

const platform =
  Platform.OS === "ios" || Platform.OS === "android" ? Platform.OS : "web";
export function paywall() {
  return authorized(async (auth) => {
    const r = await client["/v1/paywall"].get({ ...auth, query: { platform } });
    requireSuccess(r);
    return r.json();
  });
}
export type Offer = Awaited<ReturnType<typeof paywall>>;
export function entitlement() {
  return authorized(async (auth) => {
    const r = await client["/v1/entitlements"].get(auth);
    requireSuccess(r);
    return r.json();
  });
}
export function purchase(offer: Offer) {
  return authorized(async (auth) => {
    const r =
      offer.platform === "web"
        ? await client["/v1/purchases/web/checkout"].post(auth)
        : await client["/v1/purchases/native/verify"].post({
            ...auth,
            json: {
              platform: offer.platform,
              receipt: offer.sandbox_receipt ?? "",
            },
          });
    requireSuccess(r);
    return r.json();
  });
}
