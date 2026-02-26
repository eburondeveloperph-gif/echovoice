import { render, screen } from "@testing-library/react";

import { WaveBackground } from "../components/WaveBackground";

describe("WaveBackground", () => {
  it("renders animated background container", () => {
    render(<WaveBackground />);
    expect(screen.getByRole("presentation", { hidden: true })).toBeInTheDocument();
  });
});
