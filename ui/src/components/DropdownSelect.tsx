import type { SelectHTMLAttributes } from "react";

type Option = { label: string; value: string };

type Props = SelectHTMLAttributes<HTMLSelectElement> & {
  label?: string;
  options: Option[];
};

export function DropdownSelect({ label, options, className, ...rest }: Props) {
  return (
    <label className="field">
      {label && <span>{label}</span>}
      <select className={`glass-input ${className ?? ""}`.trim()} {...rest}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
