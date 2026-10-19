//===============================
// DỰ ÁN NÀY KHÔNG SỬ DỤNG COMPONENT NÀY
//===============================

// import React, { useEffect } from 'react';
// import ReactDOM from 'react-dom';

// interface ModalProps {
//     isShowingModal: boolean;
//     toggleModal: () => void;
//     children: React.ReactNode;
//     title: string;
//     size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | 'max';
// }

// const sizeClasses = {
//   sm: 'max-w-sm',
//   md: 'max-w-md',
//   lg: 'max-w-lg',
//   xl: 'max-w-xl',
//   '2xl': 'max-w-2xl',
//   '3xl': 'max-w-3xl',
//   '4xl': 'max-w-4xl',
//   '5xl': 'max-w-5xl',
//   max: 'max-w-full m-4',
// };

// const AppModal = ({ isShowingModal, toggleModal, children, title, size = 'md' }: ModalProps) => {
//   useEffect(() => {
//     if (isShowingModal) {
//       document.body.style.overflow = 'hidden';
//     } else {
//       document.body.style.overflow = 'unset';
//     }
//     return () => {
//       document.body.style.overflow = 'unset';
//     };
//   }, [isShowingModal]);

//   if (!isShowingModal) return null;

//   return (
//     ReactDOM.createPortal(
//       <React.Fragment>
//         <div className="fixed inset-0 z-50 overflow-y-auto">
//           <div className="flex min-h-full items-center justify-center p-4 sm:p-0">
//             {/* Overlay */}
//             <div
//               className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"
//               onClick={toggleModal}
//             />

//             {/* Modal Content */}
//             <div className={`relative z-10 w-full ${sizeClasses[size]} transform transition-all my-8`}>
//               <button
//                 onClick={toggleModal}
//                 className="cursor-pointer absolute top-4 right-4 z-20 p-2 text-gray-600 dark:text-gray-200 hover:text-gray-800 dark:hover:text-gray-200 rounded-full hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
//               >
//                 <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
//                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
//                 </svg>
//               </button>
//               {children}
//             </div>
//           </div>
//         </div>
//       </React.Fragment>, document.body,
//     )
//   );
// };

// export default AppModal;
