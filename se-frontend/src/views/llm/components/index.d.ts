// 仅在 TS 项目需要，可删除
declare global {
    interface Window {
        $router?: import('vue-router').Router;
    }
}
export {};