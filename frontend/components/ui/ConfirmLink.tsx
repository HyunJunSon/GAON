'use client';

import { useState, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
  DialogFooter, DialogClose
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { conversationIdStorage } from '@/utils/conversationIdStorage';

type ConfirmLinkProps = {
  href: string;
  className?: string;
  children: React.ReactNode;
  confirmTitle?: string;
  confirmDesc?: string;
};

export default function ConfirmLink({
  href,
  className,
  children,
  confirmTitle = '정말 이동할까요?',
  confirmDesc = '이동하면 기존 대화 분석결과가 사라집니다.'
}: ConfirmLinkProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);

  const handleLinkClick = useCallback((e: React.MouseEvent<HTMLAnchorElement>) => {
    // 새 탭/새 창 등 사용자의 의도를 존중
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button === 1) return;

    e.preventDefault();
    setOpen(true);
  }, []);

  const handleConfirm = useCallback(() => {
    conversationIdStorage.clear();
    setOpen(false);
    router.push(href);
  }, [href, router]);

  return (
    <>
      {/* Link 자체를 쓰되, 클릭을 가로채서 모달 오픈 */}
      <Link href={href} onClick={handleLinkClick} className={className} prefetch={false}>
        {children}
      </Link>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{confirmTitle}</DialogTitle>
            <DialogDescription>{confirmDesc}</DialogDescription>
          </DialogHeader>

          <DialogFooter className="gap-3">
            <DialogClose asChild>
              <Button variant="secondary">취소</Button>
            </DialogClose>
            <Button onClick={handleConfirm}>확인</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}