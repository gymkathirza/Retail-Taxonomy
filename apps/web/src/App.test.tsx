import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

const listZones = vi.fn();
const deleteZone = vi.fn();
const restoreZone = vi.fn();

vi.mock("./api/client", () => ({
  api: {
    listZones: (...args: unknown[]) => listZones(...args),
    listDepartments: vi.fn().mockResolvedValue({ items: [] }),
    listCategories: vi.fn().mockResolvedValue({ items: [] }),
    listSubcategories: vi.fn().mockResolvedValue({ items: [] }),
    createZone: vi.fn(),
    createDepartment: vi.fn(),
    createCategory: vi.fn(),
    createSubcategory: vi.fn(),
    updateZone: vi.fn(),
    updateDepartment: vi.fn(),
    updateCategory: vi.fn(),
    updateSubcategory: vi.fn(),
    deleteZone: (...args: unknown[]) => deleteZone(...args),
    deleteDepartment: vi.fn(),
    deleteCategory: vi.fn(),
    deleteSubcategory: vi.fn(),
    restoreZone: (...args: unknown[]) => restoreZone(...args),
    restoreDepartment: vi.fn(),
    restoreCategory: vi.fn(),
    restoreSubcategory: vi.fn(),
  },
}));

describe("Taxonomy UI", () => {
  beforeEach(() => {
    listZones.mockResolvedValue({
      items: [
        {
          id: "z1",
          name: "Center",
          description: null,
          is_active: true,
          created_at: "",
          updated_at: "",
        },
      ],
    });
    deleteZone.mockResolvedValue(undefined);
    restoreZone.mockResolvedValue({
      id: "z1",
      name: "Center",
      description: null,
      is_active: true,
      created_at: "",
      updated_at: "",
    });
    vi.spyOn(window, "confirm").mockReturnValue(true);
  });

  it("renders zones from the API", async () => {
    render(<App />);
    expect(await screen.findByText("Center")).toBeInTheDocument();
    expect(screen.getByLabelText(/show inactive/i)).toBeInTheDocument();
  });

  it("confirms before retire and calls delete", async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("Center");
    await user.click(screen.getByText("Center"));
    await user.click(screen.getByRole("button", { name: "Retire" }));
    expect(window.confirm).toHaveBeenCalled();
    expect(deleteZone).toHaveBeenCalledWith("z1");
  });
});
