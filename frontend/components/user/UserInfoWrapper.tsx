'use client';

import dynamic from "next/dynamic";

const UserInfo = dynamic(() => import("./UserInfo").then(mod => ({ default: mod.UserInfo })), {
  ssr: false
});

export function UserInfoWrapper() {
  return <UserInfo />;
}
