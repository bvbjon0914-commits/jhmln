import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
}

export function Button({
  variant = "primary",
  className = "",
  children,
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded font-medium text-sm px-4 py-2.5 transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none";

  const variants: Record<string, string> = {
    primary: "bg-brand text-white shadow-sm hover:bg-brand-dark hover:shadow-md active:shadow-sm",
    secondary:
      "bg-surface text-ink border border-line hover:border-brand/40 hover:shadow-sm",
    ghost: "text-brand hover:bg-brand-light",
  };

  return (
    <button className={`${base} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
}
