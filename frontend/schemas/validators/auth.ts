/**
 * 로그인/회원가입에서 재사용 가능한 Zod 스키마 정의
 * - 런타임 검증 + 타입 안전 동시 확보
 */
import { z } from 'zod';

/** 비밀번호 규칙:
 * - 길이: 8~16자
 * - 반드시 포함: 영문 1+, 숫자 1+, 특수문자 1+ (허용: $ ` ~ ! @ $ ! % * # ^ ? & ( ) - _ = +)
 * - 전체 허용 문자도 위 집합으로 제한
 */
const PASSWORD_REGEX =
  /^(?=.*[A-Za-z])(?=.*\d)(?=.*[`~!@\$!%*#^?&()\-\_=+])[A-Za-z\d`~!@\$!%*#^?&()\-\_=+]{8,16}$/;

export const LoginSchema = z.object({
  email: z.email('올바른 이메일 형식이 아닙니다.'),
  password: z.string().min(8, '비밀번호는 8자 이상이어야 합니다.')
})
export type LoginInput = z.infer<typeof LoginSchema>;

export const SignupSchema = z
  .object({
    // 성명 규칙 : 공백 제거 후 최소 1자, 최대 20자
    name: z.string().trim().min(1, '성명을 입력해 주세요.').max(20, '성명은 최대 20자까지 가능합니다.'),
    email: z.email('올바른 이메일 형식이 아닙니다.'),
    birthdate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, '생년월일은 YYYY-MM-DD 형식이어야 합니다.'),
    gender: z.enum(['Male', 'Female', 'Other'], { message: '성별을 선택해 주세요.' }),
    password: z.string().regex(PASSWORD_REGEX, '비밀번호는 8~16자이며 영문, 숫자, 특수문자를 각각 1자 이상 포함해야 합니다.'),
    confirmPassword: z.string(),
    termsAgreed: z.boolean().refine((v) => v === true, { message: '이용약관에 동의해야 합니다.' })
  })
  .refine((v) => v.password === v.confirmPassword, {
    message: '비밀번호가 일치하지 않습니다.',
    path: ['confirmPassword'],
  });

export type SignupInput = z.infer<typeof SignupSchema>;