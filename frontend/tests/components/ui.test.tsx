import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { UrgencyBadge } from "@/components/ui/UrgencyBadge";

describe("Button", () => {
  it("renders with primary variant by default", () => {
    render(<Button>Click me</Button>);
    const button = screen.getByRole("button", { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(button.className).toContain("bg-[#357A53]");
  });

  it("renders as anchor when asChild is true", () => {
    render(
      <Button asChild>
        <a href="/test">Link</a>
      </Button>,
    );
    const link = screen.getByRole("link", { name: /link/i });
    expect(link).toBeInTheDocument();
    expect(link.tagName).toBe("A");
  });

  it("applies disabled attribute", () => {
    render(<Button disabled>Disabled</Button>);
    const button = screen.getByRole("button", { name: /disabled/i });
    expect(button).toBeDisabled();
  });

  it("calls onClick handler", () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    fireEvent.click(screen.getByRole("button", { name: /click/i }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

describe("Card", () => {
  it("renders title and children", () => {
    render(
      <Card title="Test Card">
        <p>Card content</p>
      </Card>,
    );
    expect(screen.getByText("Test Card")).toBeInTheDocument();
    expect(screen.getByText("Card content")).toBeInTheDocument();
  });

  it("renders footer when provided", () => {
    render(
      <Card title="Card" footer={<span>Footer text</span>}>
        <p>Content</p>
      </Card>,
    );
    expect(screen.getByText("Footer text")).toBeInTheDocument();
  });

  it("omits footer element when footer prop is absent", () => {
    render(
      <Card title="Card">
        <p>Content</p>
      </Card>,
    );
    expect(screen.queryByText(/footer/i)).not.toBeInTheDocument();
  });
});

describe("Input", () => {
  it("renders visible label linked to input", () => {
    render(<Input label="Email" value="" onChange={() => {}} />);
    const label = screen.getByText("Email");
    expect(label).toBeInTheDocument();
    expect(label.tagName).toBe("LABEL");
    const input = screen.getByRole("textbox");
    expect(label.getAttribute("for")).toBe(input.id);
  });

  it("shows error message with role alert and sets aria-invalid", () => {
    render(<Input label="Email" value="" onChange={() => {}} error="Required field" />);
    const error = screen.getByRole("alert");
    expect(error).toHaveTextContent("Required field");
    const input = screen.getByRole("textbox");
    expect(input).toHaveAttribute("aria-invalid", "true");
  });

  it("shows hint text with aria-describedby", () => {
    render(<Input label="Email" value="" onChange={() => {}} hint="Enter your email" />);
    const hint = screen.getByText("Enter your email");
    expect(hint).toBeInTheDocument();
    const input = screen.getByRole("textbox");
    const describedBy = input.getAttribute("aria-describedby");
    expect(describedBy).toBeTruthy();
    expect(hint.id).toBe(describedBy);
  });
});

describe("UrgencyBadge", () => {
  it("renders correct label for each urgency level", () => {
    const { rerender } = render(<UrgencyBadge urgency="EMERGENCY" />);
    expect(screen.getByText("Emergency")).toBeInTheDocument();

    rerender(<UrgencyBadge urgency="URGENT" />);
    expect(screen.getByText("Urgent")).toBeInTheDocument();

    rerender(<UrgencyBadge urgency="ROUTINE" />);
    expect(screen.getByText("Routine")).toBeInTheDocument();

    rerender(<UrgencyBadge urgency="SELF_CARE" />);
    expect(screen.getByText("Self-care")).toBeInTheDocument();
  });

  it("applies emergency color class", () => {
    render(<UrgencyBadge urgency="EMERGENCY" />);
    const badge = screen.getByText("Emergency");
    expect(badge.className).toContain("emergency-pulse");
    expect(badge.style.color).toBe("rgb(181, 45, 36)");
  });

  it("applies routine color class", () => {
    render(<UrgencyBadge urgency="ROUTINE" />);
    const badge = screen.getByText("Routine");
    expect(badge.style.color).toBe("rgb(53, 122, 83)");
  });
});
