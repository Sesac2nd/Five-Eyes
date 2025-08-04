/**
 * 네비게이션 배열을 React Router의 routes 형태로 변환
 * @param {Array} navigation - 네비게이션 설정 배열
 * @returns {Array} React Router routes 배열
 */
export const configRoutes = (navigation) => {
  return navigation.map((route) => {
    const { text, ...routeConfig } = route;

    // children이 있는 경우 재귀적으로 처리
    if (route.children) {
      routeConfig.children = configRoutes(route.children);
    }

    return routeConfig;
  });
};

/**
 * 네비게이션 아이템들에서 메뉴에 표시할 항목들만 추출
 * @param {Array} navigation - 네비게이션 설정 배열
 * @returns {Array} 메뉴 표시용 네비게이션 아이템들
 */
export const getNavigationItems = (navigation) => {
  return navigation
    .filter((item) => !item.hideInMenu) // hideInMenu가 true인 항목 제외
    .map((item) => ({
      text: item.text,
      path: item.path || "/",
      icon: item.icon,
      description: item.description,
      children: item.children ? getNavigationItems(item.children) : undefined,
    }));
};

/**
 * 페이지 제목을 동적으로 설정
 * @param {string} title - 페이지 제목
 */
export const setPageTitle = (title) => {
  document.title = title ? `${title} - 역사로` : "역사로(HistPath) - AI 기반 한국사 고증 검색 플랫폼";
};

/**
 * 검색 쿼리 파라미터 파싱
 * @param {URLSearchParams} searchParams - URL 검색 파라미터
 * @returns {Object} 파싱된 쿼리 객체
 */
export const parseSearchParams = (searchParams) => {
  const query = {};
  for (const [key, value] of searchParams.entries()) {
    query[key] = value;
  }
  return query;
};

/**
 * 파일 크기를 사람이 읽기 쉬운 형태로 변환
 * @param {number} bytes - 바이트 크기
 * @returns {string} 변환된 크기 문자열
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

/**
 * 디바운스 함수
 * @param {Function} func - 실행할 함수
 * @param {number} delay - 지연 시간 (ms)
 * @returns {Function} 디바운스된 함수
 */
export const debounce = (func, delay) => {
  let timeoutId;
  return (...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(null, args), delay);
  };
};
