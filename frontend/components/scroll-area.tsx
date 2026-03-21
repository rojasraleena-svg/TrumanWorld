"use client";

import {
  forwardRef,
  type HTMLAttributes,
  useEffect,
  useRef,
} from "react";

type ScrollAreaProps = HTMLAttributes<HTMLElement> & {
  as?: "div" | "aside";
};

export const ScrollArea = forwardRef<HTMLElement, ScrollAreaProps>(function ScrollArea(
  {
    as: Component = "div",
    className,
    children,
    onScroll,
    ...props
  },
  forwardedRef,
) {
  const areaRef = useRef<HTMLElement | null>(null);
  const hideTimerRef = useRef<number | null>(null);

  useEffect(() => {
    const element = areaRef.current;
    if (!element) return;

    const updateOverflow = () => {
      const hasVerticalOverflow = element.scrollHeight - element.clientHeight > 1;
      const hasHorizontalOverflow = element.scrollWidth - element.clientWidth > 1;
      element.classList.toggle("has-overflow", hasVerticalOverflow || hasHorizontalOverflow);
    };

    updateOverflow();
    const rafId = window.requestAnimationFrame(updateOverflow);
    const resizeObserver = new ResizeObserver(updateOverflow);
    resizeObserver.observe(element);

    const mutationObserver = new MutationObserver(updateOverflow);
    mutationObserver.observe(element, {
      childList: true,
      subtree: true,
      characterData: true,
    });

    window.addEventListener("resize", updateOverflow);

    return () => {
      window.cancelAnimationFrame(rafId);
      window.removeEventListener("resize", updateOverflow);
      resizeObserver.disconnect();
      mutationObserver.disconnect();
      if (hideTimerRef.current) {
        window.clearTimeout(hideTimerRef.current);
      }
    };
  }, []);

  const setRefs = (node: HTMLElement | null) => {
    areaRef.current = node;
    if (typeof forwardedRef === "function") {
      forwardedRef(node);
    } else if (forwardedRef) {
      forwardedRef.current = node;
    }
  };

  const handleScroll: NonNullable<HTMLAttributes<HTMLElement>["onScroll"]> = (event) => {
    const element = areaRef.current;
    if (element) {
      element.classList.add("scroll-active");
      if (hideTimerRef.current) {
        window.clearTimeout(hideTimerRef.current);
      }
      hideTimerRef.current = window.setTimeout(() => {
        element.classList.remove("scroll-active");
      }, 420);
      const hasVerticalOverflow = element.scrollHeight - element.clientHeight > 1;
      const hasHorizontalOverflow = element.scrollWidth - element.clientWidth > 1;
      element.classList.toggle("has-overflow", hasVerticalOverflow || hasHorizontalOverflow);
    }

    onScroll?.(event);
  };

  return (
    <Component
      ref={setRefs}
      onScroll={handleScroll}
      className={["scrollbar-soft", "scroll-fade-y", className].filter(Boolean).join(" ")}
      {...props}
    >
      {children}
    </Component>
  );
});
