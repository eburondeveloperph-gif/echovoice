type Props = {
  checked: boolean;
  onChange: (value: boolean) => void;
  label: string;
};

export function ToggleSwitch({ checked, onChange, label }: Props) {
  return (
    <label className="toggle-switch">
      <span>{label}</span>
      <button
        type="button"
        className={`toggle-button ${checked ? "on" : "off"}`}
        onClick={() => onChange(!checked)}
      >
        <span className="toggle-knob" />
      </button>
    </label>
  );
}
