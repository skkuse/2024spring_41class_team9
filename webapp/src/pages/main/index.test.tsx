import React from "react";
import { render, screen } from "@testing-library/react";
import MainPage from "./index";

test("renders main page", () => {
  render(<MainPage />);
  const linkElement = screen.getByText(/learn react/i);
  expect(linkElement).toBeInTheDocument();
});
