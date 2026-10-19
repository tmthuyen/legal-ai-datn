# AGENTS.md 

Hướng dẫn chung cho AI coding agent khi làm việc trong thư mục frontend/ của dự án LegalAI.

## Dự án

- Đây là dự án về Luật suy luận kiếm chứng và trích dẫn pháp lý
- Code trong thư mục này (frontend) là tầng UI ứng dụng của dự án
- Kết nối và giao tiếp với API từ backend(FastAPI) và services (Golang)
- Các thành phân giao diện không liên quan đến chủ để pháp luật sẽ không được dùng với render (vì trong này chưa code dự án khác)
- Các trang Auth, About, Contact, Profile, Các layout Header, Nav, Sidebar: đều là page, components phổ biến, nếu có thể sử dụng
- Các components khác cũng có thể tái sử dụng nếu dùng chung không bị phụ thuộc

## Công nghệ sử dụng

- Viết bằng NextJS và sử dụng Shadcn UI + Tailwindcss + TypeScript
- Công nghệ chi tiết trong `package.json` và `tsconfig.json`

## Các tài liệu dự án

- Thư mục `docs/`: Tài liệu tổng quan về đồ án, các hướng dẫn, các summary, plans
- Agent làm việc phải nắm rõ các markdown trong thư mục trên để hiểu dự án
- Khi viết code tính năng mới phải chia viết Plan chia các phase

## Các quy ước Rules khi code

- Tuân thủ các Rules (đã viết trong `docs` với các Rules đã yêu cầu)
- Tuân thủ các API từ hệ thống server: cấm bịa kiểu trả về phải luôn tuân thủ dể render UI
- Nhận yêu cầu và viết plan để review và thực hiện task theo phase, tuân thủ cách viết plan đã quy định
