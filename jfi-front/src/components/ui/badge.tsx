import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-indigo-600 text-white shadow-sm",
        secondary:
          "border-transparent bg-stone-100 text-stone-700",
        destructive:
          "border-transparent bg-rose-500 text-white shadow-sm",
        outline: "text-stone-700 border-stone-200",
        subtle: "border-indigo-100 bg-indigo-50/80 text-indigo-700 font-medium",
        success: "border-emerald-100 bg-emerald-50 text-emerald-700 font-medium",
        warning: "border-amber-100 bg-amber-50 text-amber-700 font-medium",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
