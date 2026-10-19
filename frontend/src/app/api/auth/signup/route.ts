import { NextRequest, NextResponse } from 'next/server';

// NOTE: Route stub — màn hình đăng ký gọi thẳng backend qua `authApi.register`
// (xem src/apis/auth.api.ts → POST /auth/register trên API gateway).
// Route này chỉ giữ tương thích; không chứa logic đăng ký thật.
export const POST = async (req: NextRequest) => {
  return NextResponse.json(
    {
      success: true,
      statusCode: 201,
      message: 'Signup successful',
      result: {},
    },
    { status: 201 },
  );
};
