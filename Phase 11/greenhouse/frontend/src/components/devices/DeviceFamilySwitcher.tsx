type Props = {
  family: "simulation" | "edge";
  setFamily: (x: "simulation" | "edge") => void;
};

export default function DeviceFamilySwitcher({
  family,
  setFamily,
}: Props) {
  const families: ("simulation" | "edge")[] = [
    "simulation",
    "edge",
  ];

  return (
    <div className="flex gap-3">
      {families.map((f) => (
        <button
          key={f}
          onClick={() => setFamily(f)}
          className={`border rounded px-4 py-2 capitalize ${
            family === f
              ? "bg-green-600 text-white"
              : "bg-white"
          }`}
        >
          {f}
        </button>
      ))}
    </div>
  );
}