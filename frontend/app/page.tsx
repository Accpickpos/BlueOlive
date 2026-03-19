'use client';

import { ArrowRight, BarChart3, Users, Lock, Zap, Globe, TrendingUp, Check } from 'lucide-react';
import Link from 'next/link';
import { useAuthContext } from '@/lib/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { getActiveSubscriptionPlans } from '@/lib/api';

export default function LandingPage() {
  const { user, isLoading } = useAuthContext();
  const router = useRouter();
  const [plans, setPlans] = useState<any[]>([]);
  const [plansLoading, setPlansLoading] = useState(true);

  // Redirect if already logged in
  useEffect(() => {
    if (!isLoading && user) {
      router.push('/dashboard');
    }
  }, [user, isLoading, router]);

  // Fetch subscription plans
  useEffect(() => {
    async function fetchPlans() {
      try {
        const data = await getActiveSubscriptionPlans();
        setPlans(data);
      } catch (error) {
        console.error('Failed to fetch plans:', error);
        // Fallback to default plans if API fails
        setPlans([
          {
            id: 1,
            name: 'Starter',
            price: 99,
            description: 'Perfect for small businesses',
            features: { pos: true, debtors: false, creditors: false, api_access: false },
            max_shops: 1,
            max_users: 3,
          },
          {
            id: 2,
            name: 'Professional',
            price: 249,
            description: 'For growing businesses',
            features: { pos: true, debtors: true, creditors: false, api_access: false },
            max_shops: 3,
            max_users: 10,
          },
          {
            id: 3,
            name: 'Enterprise',
            price: 499,
            description: 'Full-featured for large operations',
            features: { pos: true, debtors: true, creditors: true, api_access: true },
            max_shops: 999,
            max_users: 50,
          },
        ]);
      } finally {
        setPlansLoading(false);
      }
    }
    fetchPlans();
  }, []);

  return (
    <div className="min-h-screen bg-white">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 bg-white border-b border-gray-200 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="bg-indigo-600 rounded-lg p-2">
                <BarChart3 className="h-6 w-6 text-white" />
              </div>
              <span className="text-2xl font-bold text-gray-900">BlueOlive</span>
            </div>
            
            <div className="flex items-center gap-4">
              <Link 
                href="/auth" 
                className="text-gray-700 hover:text-indigo-600 font-medium transition"
              >
                Login
              </Link>
              <Link 
                href="/auth" 
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg font-medium transition"
              >
                Sign Up
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            {/* Left Column - Text */}
            <div>
              <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
                Powerful Retail Management for Modern Businesses
              </h1>
              <p className="text-xl text-gray-600 mb-8 leading-relaxed">
                BlueOlive is a comprehensive multi-tenant retail management system designed for small to medium-sized businesses. Manage inventory, sales, customers, and analytics all in one place.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 mb-12">
                <Link 
                  href="/auth" 
                  className="inline-flex items-center justify-center bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-4 rounded-lg font-semibold transition gap-2"
                >
                  Get Started <ArrowRight className="h-5 w-5" />
                </Link>
                <button 
                  onClick={() => {
                    document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
                  }}
                  className="inline-flex items-center justify-center bg-gray-100 hover:bg-gray-200 text-gray-900 px-8 py-4 rounded-lg font-semibold transition"
                >
                  Learn More
                </button>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-6">
                <div>
                  <div className="text-3xl font-bold text-indigo-600">99.9%</div>
                  <p className="text-gray-600 text-sm">Uptime</p>
                </div>
                <div>
                  <div className="text-3xl font-bold text-indigo-600">500+</div>
                  <p className="text-gray-600 text-sm">Active Users</p>
                </div>
                <div>
                  <div className="text-3xl font-bold text-indigo-600">24/7</div>
                  <p className="text-gray-600 text-sm">Support</p>
                </div>
              </div>
            </div>

            {/* Right Column - Visual */}
            <div className="relative h-96 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-2xl shadow-xl p-8 flex items-center justify-center">
              <div className="space-y-4 w-full">
                <div className="bg-white rounded-lg p-4 shadow-md">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-semibold text-gray-800">Live Dashboard</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs text-gray-600">
                      <span>Total Sales</span>
                      <span>$24,580</span>
                    </div>
                    <div className="bg-gray-200 rounded-full h-2">
                      <div className="bg-indigo-600 h-2 rounded-full" style={{ width: '75%' }}></div>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white rounded-lg p-4 shadow-md">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-sm font-semibold text-gray-800">Inventory Status</span>
                  </div>
                  <div className="text-xs text-gray-600">Items in Stock: 2,341</div>
                </div>
                
                <div className="bg-white rounded-lg p-4 shadow-md">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                    <span className="text-sm font-semibold text-gray-800">Recent Orders</span>
                  </div>
                  <div className="text-xs text-gray-600">5 new orders today</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">Powerful Features</h2>
            <p className="text-xl text-gray-600">Everything you need to run your retail business efficiently</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white rounded-xl shadow-md p-8 hover:shadow-lg transition">
              <div className="bg-indigo-100 rounded-lg p-3 w-fit mb-4">
                <BarChart3 className="h-6 w-6 text-indigo-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Advanced Analytics</h3>
              <p className="text-gray-600">Get real-time insights into your sales, inventory, and customer behavior with detailed dashboards and reports.</p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white rounded-xl shadow-md p-8 hover:shadow-lg transition">
              <div className="bg-green-100 rounded-lg p-3 w-fit mb-4">
                <Users className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Multi-Tenant Support</h3>
              <p className="text-gray-600">Manage multiple shops and locations from a single platform with complete data isolation and security.</p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white rounded-xl shadow-md p-8 hover:shadow-lg transition">
              <div className="bg-purple-100 rounded-lg p-3 w-fit mb-4">
                <Lock className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Enterprise Security</h3>
              <p className="text-gray-600">Role-based access control, JWT authentication, and encrypted data storage for maximum security.</p>
            </div>

            {/* Feature 4 */}
            <div className="bg-white rounded-xl shadow-md p-8 hover:shadow-lg transition">
              <div className="bg-blue-100 rounded-lg p-3 w-fit mb-4">
                <Zap className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Fast & Reliable</h3>
              <p className="text-gray-600">Built on modern technology stack with 99.9% uptime guarantee and lightning-fast performance.</p>
            </div>

            {/* Feature 5 */}
            <div className="bg-white rounded-xl shadow-md p-8 hover:shadow-lg transition">
              <div className="bg-orange-100 rounded-lg p-3 w-fit mb-4">
                <Globe className="h-6 w-6 text-orange-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Cloud-Based</h3>
              <p className="text-gray-600">Access your business data anywhere, anytime with our secure cloud infrastructure.</p>
            </div>

            {/* Feature 6 */}
            <div className="bg-white rounded-xl shadow-md p-8 hover:shadow-lg transition">
              <div className="bg-red-100 rounded-lg p-3 w-fit mb-4">
                <TrendingUp className="h-6 w-6 text-red-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">Grow Your Business</h3>
              <p className="text-gray-600">Tools and insights designed to help you scale your retail business and increase profitability.</p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">How It Works</h2>
            <p className="text-xl text-gray-600">Get started in minutes with our simple onboarding process</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {[
              { step: '1', title: 'Sign Up', desc: 'Create your account and register your company' },
              { step: '2', title: 'Setup', desc: 'Configure your shops and user permissions' },
              { step: '3', title: 'Connect', desc: 'Link your inventory and products' },
              { step: '4', title: 'Manage', desc: 'Start managing your retail business' },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="bg-indigo-600 text-white rounded-full w-16 h-16 flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                  {item.step}
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">{item.title}</h3>
                <p className="text-gray-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">Simple, Transparent Pricing</h2>
            <p className="text-xl text-gray-600">Choose the plan that fits your business needs</p>
          </div>

          {plansLoading ? (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              {plans.map((plan: any) => (
                <div key={plan.id} className="bg-white rounded-2xl shadow-lg p-8 hover:shadow-xl transition border-2 border-transparent hover:border-indigo-600">
                  <div className="text-center">
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                    <p className="text-gray-600 mb-6">{plan.description || plan.name + ' plan'}</p>
                    <div className="mb-6">
                      <span className="text-4xl font-bold text-gray-900">R{plan.price}</span>
                      <span className="text-gray-600">/shop/month</span>
                    </div>
                  </div>
                  
                  <ul className="space-y-4 mb-8">
                    <li className="flex items-center gap-3">
                      <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                      <span className="text-gray-700">Up to {plan.max_shops === 999 ? 'Unlimited' : plan.max_shops} shops</span>
                    </li>
                    <li className="flex items-center gap-3">
                      <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                      <span className="text-gray-700">Up to {plan.max_users} users</span>
                    </li>
                    {plan.features?.pos && (
                      <li className="flex items-center gap-3">
                        <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                        <span className="text-gray-700">POS System</span>
                      </li>
                    )}
                    {plan.features?.debtors && (
                      <li className="flex items-center gap-3">
                        <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                        <span className="text-gray-700">Debtors Management</span>
                      </li>
                    )}
                    {plan.features?.creditors && (
                      <li className="flex items-center gap-3">
                        <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                        <span className="text-gray-700">Creditors Management</span>
                      </li>
                    )}
                    {plan.features?.api_access && (
                      <li className="flex items-center gap-3">
                        <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                        <span className="text-gray-700">API Access</span>
                      </li>
                    )}
                  </ul>

                  <Link
                    href="/auth"
                    className="block w-full text-center bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-lg font-semibold transition"
                  >
                    Get Started
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-indigo-600 to-purple-600">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">Ready to Transform Your Retail Business?</h2>
          <p className="text-xl text-indigo-100 mb-8">Join hundreds of successful businesses using BlueOlive</p>
          <Link 
            href="/auth" 
            className="inline-flex items-center justify-center bg-white hover:bg-gray-100 text-indigo-600 px-8 py-4 rounded-lg font-semibold transition gap-2"
          >
            Get Started Free <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="bg-indigo-600 rounded-lg p-2">
                  <BarChart3 className="h-5 w-5 text-white" />
                </div>
                <span className="text-xl font-bold text-white">BlueOlive</span>
              </div>
              <p className="text-sm">Professional retail management for modern businesses.</p>
            </div>
            
            <div>
              <h4 className="text-white font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#features" className="hover:text-white transition">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition">Pricing</a></li>
                <li><a href="#" className="hover:text-white transition">Security</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-white font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white transition">About</a></li>
                <li><a href="#" className="hover:text-white transition">Blog</a></li>
                <li><a href="#" className="hover:text-white transition">Contact</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-white font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white transition">Privacy</a></li>
                <li><a href="#" className="hover:text-white transition">Terms</a></li>
                <li><a href="#" className="hover:text-white transition">Support</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 pt-8">
            <p className="text-center text-sm">&copy; 2026 BlueOlive. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
