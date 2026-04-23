import sgMail from '@sendgrid/mail';

sgMail.setApiKey(process.env.SENDGRID_API_KEY!);

export async function sendWelcomeEmail(to: string, name: string) {
    const msg = {
        to,
        from: 'noreply@myapp.com',
        subject: 'Welcome to MyApp!',
        text: `Hi ${name}, welcome to our platform!`,
        html: `<strong>Hi ${name}, welcome to our platform!</strong>`,
    };
    await sgMail.send(msg);
}\n