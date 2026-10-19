//===============================
// DỰ ÁN NÀY KHÔNG SỬ DỤNG COMPONENT NÀY
//===============================

// import React, { Component, type ErrorInfo, type ReactNode } from 'react';
// import { AlertTriangle, RefreshCcw } from 'lucide-react';
// import { Button } from '@/components/ui/button';

// interface Props {
//   children?: ReactNode;
// }

// interface State {
//   hasError: boolean;
//   error: Error | null;
// }

// class ErrorBoundary extends Component<Props, State> {
//   public state: State = {
//     hasError: false,
//     error: null,
//   };

//   public static getDerivedStateFromError(error: Error): State {
//     return { hasError: true, error };
//   }

//   public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
//     console.error('Uncaught error:', error, errorInfo);
//   }

//   private handleReload = () => {
//     window.location.reload();
//   };

//   public render() {
//     if (this.state.hasError) {
//       return (
//         <div className="m-8 min-h-screen flex flex-col items-center justify-center p-8 bg-gray-50 dark:bg-slate-900 rounded-2xl border border-red-200 dark:border-red-900/50 ">
//           <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mb-6">
//             <AlertTriangle className="w-8 h-8 text-red-500" />
//           </div>
//           <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
//             Đã có lỗi xảy ra!
//           </h2>
//           <p className="text-gray-500 dark:text-gray-400 text-center max-w-md mb-6">
//             Rất xin lỗi, thành phần giao diện này đang gặp sự cố. Bạn vui lòng
//             thử tải lại trang.
//           </p>

//           {import.meta.env.MODE === 'development' && this.state.error && (
//             <div className="w-full max-w-2xl bg-gray-900 rounded-lg p-4 mb-6 overflow-auto">
//               <pre className="text-red-400 text-xs font-mono text-left">
//                 {this.state.error.toString()}
//               </pre>
//             </div>
//           )}

//           <Button
//             onClick={this.handleReload}
//             className="bg-red-500 hover:bg-red-600 text-white rounded-xl shadow-lg shadow-red-500/20"
//           >
//             <RefreshCcw className="w-4 h-4 mr-2" />
//             Tải lại trang
//           </Button>
//         </div>
//       );
//     }

//     return this.props.children;
//   }
// }

// export default ErrorBoundary;
