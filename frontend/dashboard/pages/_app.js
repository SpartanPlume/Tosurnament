import "../scss/custom.scss";
import "../styles/globals.css";
import "react-toastify/dist/ReactToastify.css";

import { ToastContainer } from "react-toastify";
import { QueryClient, QueryClientProvider } from "react-query";
import Header from "../components/Header";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (count, error) => {
        const status = error?.response?.status;
        return status !== 401 && status !== 403 && status !== 404;
      }
    }
  }
});

export default function MyApp({ Component, pageProps }) {
  return (
    <QueryClientProvider client={queryClient}>
      <Header />
      <div className="page">
        <Component {...pageProps} />
      </div>
      <ToastContainer theme="dark" position="bottom-right" autoClose={3000} hideProgressBar />
    </QueryClientProvider>
  );
}
