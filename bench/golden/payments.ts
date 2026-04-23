import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
    apiVersion: '2023-10-16',
});

export async function createPaymentIntent(amount: number, currency: string) {
    return await stripe.paymentIntents.create({
        amount,
        currency,
        automatic_payment_methods: { enabled: true },
    });
}\n