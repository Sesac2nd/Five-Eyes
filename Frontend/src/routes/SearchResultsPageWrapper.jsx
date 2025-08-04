// src/routes/SearchResultsPageWrapper.jsx
import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import SearchResultsPage from "@/pages/SearchResultsPage";
import { setPageTitle } from "@/utils";

function SearchResultsPageWrapper() {
  const [searchParams] = useSearchParams();
  const query = searchParams.get("q");

  useEffect(() => {
    setPageTitle(query ? `"${query}" 검색 결과` : "검색 결과");
  }, [query]);

  return <SearchResultsPage />;
}

export default SearchResultsPageWrapper;
