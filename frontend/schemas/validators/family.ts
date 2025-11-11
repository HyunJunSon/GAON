import { z } from 'zod';

/** 가족 구성원 추가: 이메일 검증 */
export const addFamilySchema = z.object({
  email: z.email('올바른 이메일 형식이 아닙니다.')
})

export type AddFamilyInput = z.infer<typeof addFamilySchema>