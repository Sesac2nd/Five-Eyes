import { RouterProvider } from "react-router-dom";
import { DarkModeProvider } from "@/contexts/DarkModeContext";
import router from "@/router/router";

function App() {
  return (
    <DarkModeProvider>
      <RouterProvider router={router} />
    </DarkModeProvider>
  );
}

export default App;
