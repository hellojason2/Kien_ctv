import { useEffect, useRef, useState } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { 
  Menu, X, ChevronDown, ChevronUp, Phone, Calendar, 
  Users, ArrowRight, CheckCircle2,
  Sparkles, Heart
} from 'lucide-react';
import './App.css';

gsap.registerPlugin(ScrollTrigger);

// Intro Animation Component
function IntroAnimation({ onComplete }: { onComplete: () => void }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const logoRef = useRef<HTMLDivElement>(null);
  const circleRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({
        onComplete: () => {
          gsap.to(containerRef.current, {
            opacity: 0,
            duration: 0.5,
            onComplete
          });
        }
      });

      tl.from(circleRef.current, {
        scale: 0,
        duration: 0.8,
        ease: 'back.out(1.7)'
      })
      .from(logoRef.current, {
        scale: 0.5,
        opacity: 0,
        duration: 0.6,
        ease: 'power2.out'
      }, '-=0.4')
      .from(textRef.current?.querySelectorAll('.char') || [], {
        y: 50,
        opacity: 0,
        duration: 0.5,
        stagger: 0.03,
        ease: 'power2.out'
      }, '-=0.3')
      .to({}, { duration: 0.8 }); // Hold before completing
    }, containerRef);

    return () => ctx.revert();
  }, [onComplete]);

  const brandText = 'TAM GROUP';

  return (
    <div 
      ref={containerRef}
      className="fixed inset-0 z-[100] bg-warm-white flex items-center justify-center"
    >
      <div className="relative flex flex-col items-center">
        <div 
          ref={circleRef}
          className="w-32 h-32 rounded-full bg-accent flex items-center justify-center mb-6"
        >
          <Sparkles className="w-16 h-16 text-white" />
        </div>
        <div ref={logoRef} className="text-4xl font-display text-near-black mb-4">
          TAM GROUP
        </div>
        <div ref={textRef} className="flex">
          {brandText.split('').map((char, i) => (
            <span key={i} className="char text-6xl font-display text-near-black">
              {char === ' ' ? '\u00A0' : char}
            </span>
          ))}
        </div>
        <div className="mt-8 text-text-secondary font-mono-label">
          THẨM MỸ VIỆN TẤM
        </div>
      </div>
    </div>
  );
}

// Navigation Component
function Navigation() {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 100);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      setIsOpen(false);
    }
  };

  return (
    <>
      <nav 
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
          scrolled ? 'bg-warm-white/90 backdrop-blur-md py-4' : 'bg-transparent py-6'
        }`}
      >
        <div className="px-6 lg:px-12 flex items-center justify-between">
          <div className="font-display text-xl text-near-black cursor-pointer" onClick={() => scrollToSection('hero')}>
            TAM GROUP
          </div>
          
          <div className="hidden lg:flex items-center gap-8">
            {[
              { label: 'Trang chủ', id: 'hero' },
              { label: 'Đặt lịch', id: 'booking' },
              { label: 'Gói hội viên', id: 'membership' },
              { label: 'Liên hệ', id: 'contact' },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className="text-sm font-medium text-near-black hover:text-accent transition-colors"
              >
                {item.label}
              </button>
            ))}
            <button className="btn-outline text-sm py-2 px-6">
              Đăng nhập CTV
            </button>
          </div>
          
          <button 
            className="lg:hidden p-2"
            onClick={() => setIsOpen(true)}
          >
            <Menu className="w-6 h-6 text-near-black" />
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      <div 
        className={`fixed inset-0 z-[60] bg-near-black transition-transform duration-500 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="p-6 flex justify-end">
          <button onClick={() => setIsOpen(false)}>
            <X className="w-8 h-8 text-white" />
          </button>
        </div>
        <div className="flex flex-col items-center gap-8 pt-12">
          {[
            { label: 'Trang chủ', id: 'hero' },
            { label: 'Đặt lịch', id: 'booking' },
            { label: 'Gói hội viên', id: 'membership' },
            { label: 'Liên hệ', id: 'contact' },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => scrollToSection(item.id)}
              className="text-2xl font-display text-white hover:text-accent transition-colors"
            >
              {item.label}
            </button>
          ))}
          <button className="btn-outline-white mt-8">
            Đăng nhập CTV
          </button>
        </div>
      </div>
    </>
  );
}

// Hero Section
function HeroSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const circleRef = useRef<HTMLDivElement>(null);
  const headlineRef = useRef<HTMLDivElement>(null);
  const subRef = useRef<HTMLDivElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Entrance animation
      gsap.from(circleRef.current, {
        scale: 0.85,
        opacity: 0,
        duration: 1.1,
        ease: 'power2.out'
      });

      gsap.from(headlineRef.current?.querySelectorAll('.word') || [], {
        y: 40,
        opacity: 0,
        duration: 0.8,
        stagger: 0.1,
        ease: 'power2.out',
        delay: 0.3
      });

      gsap.from([subRef.current, ctaRef.current], {
        y: 24,
        opacity: 0,
        duration: 0.6,
        stagger: 0.08,
        ease: 'power2.out',
        delay: 0.6
      });

      // Scroll-driven exit
      ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top top',
        end: '+=130%',
        pin: true,
        scrub: 0.6,
        onUpdate: (self) => {
          const progress = self.progress;
          if (progress > 0.7) {
            const exitProgress = (progress - 0.7) / 0.3;
            gsap.set(headlineRef.current, {
              x: -18 * exitProgress + 'vw',
              opacity: 1 - exitProgress * 0.75
            });
            gsap.set(circleRef.current, {
              x: -10 * exitProgress + 'vw',
              scale: 1 + 0.08 * exitProgress,
              opacity: 1 - exitProgress * 0.65
            });
            gsap.set(ctaRef.current, {
              y: 10 * exitProgress + 'vh',
              opacity: 1 - exitProgress * 0.8
            });
          }
        },
        onLeaveBack: () => {
          gsap.set([headlineRef.current, circleRef.current, ctaRef.current, subRef.current], {
            x: 0, y: 0, scale: 1, opacity: 1
          });
        }
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section 
      id="hero"
      ref={sectionRef} 
      className="section-pinned bg-warm-white flex items-center"
    >
      <div 
        ref={circleRef}
        className="absolute left-[6vw] top-[14vh] w-[62vw] h-[62vw] circle-image z-[1]"
      >
        <img src="/hero_circle_spa.jpg" alt="Spa interior" />
      </div>
      
      <div className="relative z-10 px-[10vw] pt-[20vh]">
        <div ref={headlineRef} className="mb-6">
          <div className="red-rule mb-6" />
          <h1 className="text-hero font-display text-near-black">
            <span className="word inline-block">CHẠM</span>{' '}
            <span className="word inline-block">ĐẾN</span>
            <br />
            <span className="word inline-block">VẺ</span>{' '}
            <span className="word inline-block">ĐẸP</span>
          </h1>
        </div>
        
        <div ref={subRef} className="max-w-[34vw] mb-8">
          <p className="text-body text-text-secondary">
            Đặt lịch dễ dàng. Trải nghiệm làm đẹp được cá nhân hóa—từ da, tóc đến cơ thể.
          </p>
        </div>
        
        <div ref={ctaRef} className="flex items-center gap-6">
          <button className="btn-primary">
            <Calendar className="w-5 h-5 mr-2" />
            Đặt lịch ngay
          </button>
          <button className="text-near-black font-medium underline underline-offset-4 hover:text-accent transition-colors">
            Trở thành CTV
          </button>
        </div>
      </div>
    </section>
  );
}

// Membership Section
function MembershipSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const leftCardRef = useRef<HTMLDivElement>(null);
  const rightCardRef = useRef<HTMLDivElement>(null);
  const labelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top top',
        end: '+=130%',
        pin: true,
        scrub: 0.6,
        onUpdate: (self) => {
          const progress = self.progress;
          
          // Entrance (0-30%)
          if (progress <= 0.3) {
            const enterProgress = progress / 0.3;
            gsap.set(leftCardRef.current, {
              x: -60 * (1 - enterProgress) + 'vw',
              opacity: enterProgress,
              rotate: -2 * (1 - enterProgress)
            });
            gsap.set(rightCardRef.current, {
              x: 60 * (1 - enterProgress) + 'vw',
              opacity: enterProgress,
              rotate: 2 * (1 - enterProgress)
            });
            gsap.set(labelRef.current, {
              y: -20 * (1 - enterProgress),
              opacity: enterProgress
            });
          }
          // Settle (30-70%)
          else if (progress <= 0.7) {
            gsap.set(leftCardRef.current, { x: 0, opacity: 1, rotate: 0 });
            gsap.set(rightCardRef.current, { x: 0, opacity: 1, rotate: 0 });
            gsap.set(labelRef.current, { y: 0, opacity: 1 });
          }
          // Exit (70-100%)
          else {
            const exitProgress = (progress - 0.7) / 0.3;
            gsap.set(leftCardRef.current, {
              x: -35 * exitProgress + 'vw',
              opacity: 1 - exitProgress * 0.75
            });
            gsap.set(rightCardRef.current, {
              x: 35 * exitProgress + 'vw',
              opacity: 1 - exitProgress * 0.75
            });
            gsap.set(labelRef.current, {
              opacity: 1 - exitProgress * 0.8
            });
          }
        }
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section 
      id="membership"
      ref={sectionRef} 
      className="section-pinned bg-warm-white flex items-center justify-center"
    >
      <div ref={labelRef} className="absolute left-[6vw] top-[10vh]">
        <span className="font-mono-label text-text-secondary">01 / GÓI HỘI VIÊN</span>
      </div>
      
      <div className="flex gap-8 px-[6vw] w-full max-w-[1400px]">
        {/* Left Card - Basic */}
        <div 
          ref={leftCardRef}
          className="card-tier flex-1 bg-white p-8 flex flex-col items-center"
          style={{ minHeight: '68vh' }}
        >
          <div className="w-48 h-48 circle-image mb-8">
            <img src="/tier_basic_circle.jpg" alt="Gói cơ bản" />
          </div>
          <h3 className="text-2xl font-display text-near-black mb-4">GÓI CƠ BẢN</h3>
          <p className="text-body text-text-secondary text-center mb-8 max-w-[280px]">
            Giữ gìn vẻ đẹp hàng ngày—chăm sóc da, gội đầu thư giãn và ưu đãi giờ vàng.
          </p>
          <div className="mt-auto">
            <button className="btn-outline">Đăng ký Cơ bản</button>
          </div>
        </div>
        
        {/* Right Card - Premium */}
        <div 
          ref={rightCardRef}
          className="card-tier flex-1 bg-near-black p-8 flex flex-col items-center"
          style={{ minHeight: '68vh' }}
        >
          <div className="w-48 h-48 circle-image mb-8">
            <img src="/tier_premium_circle.jpg" alt="Gói cao cấp" />
          </div>
          <h3 className="text-2xl font-display text-white mb-4">GÓI CAO CẤP</h3>
          <p className="text-body text-white/70 text-center mb-8 max-w-[280px]">
            Trải nghiệm toàn diện—điều trị chuyên sâu, linh hoạt lịch hẹn và quyền lợi đặc biệt.
          </p>
          <div className="mt-auto">
            <button className="btn-primary">Đăng ký Cao cấp</button>
          </div>
        </div>
      </div>
    </section>
  );
}

// Feature Section Component (reusable)
function FeatureSection({ 
  id,
  label, 
  headline, 
  body, 
  cta, 
  image, 
  imagePosition = 'left'
}: { 
  id?: string;
  label: string;
  headline: string;
  body: string;
  cta: string;
  image: string;
  imagePosition?: 'left' | 'right';
}) {
  const sectionRef = useRef<HTMLDivElement>(null);
  const circleRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top top',
        end: '+=130%',
        pin: true,
        scrub: 0.6,
        onUpdate: (self) => {
          const progress = self.progress;
          const imageEnterX = imagePosition === 'left' ? -20 : 20;
          const imageExitX = imagePosition === 'left' ? -18 : 18;
          const textEnterX = imagePosition === 'left' ? 40 : -40;
          const textExitX = imagePosition === 'left' ? 18 : -18;
          
          // Entrance (0-30%)
          if (progress <= 0.3) {
            const enterProgress = progress / 0.3;
            gsap.set(circleRef.current, {
              scale: 0.65 + 0.35 * enterProgress,
              x: imageEnterX * (1 - enterProgress) + 'vw',
              opacity: enterProgress
            });
            gsap.set(textRef.current, {
              x: textEnterX * (1 - enterProgress) + 'vw',
              opacity: enterProgress
            });
          }
          // Settle (30-70%)
          else if (progress <= 0.7) {
            gsap.set(circleRef.current, { scale: 1, x: 0, opacity: 1 });
            gsap.set(textRef.current, { x: 0, opacity: 1 });
          }
          // Exit (70-100%)
          else {
            const exitProgress = (progress - 0.7) / 0.3;
            gsap.set(circleRef.current, {
              x: imageExitX * exitProgress + 'vw',
              opacity: 1 - exitProgress * 0.65
            });
            gsap.set(textRef.current, {
              x: textExitX * exitProgress + 'vw',
              opacity: 1 - exitProgress * 0.75
            });
          }
        }
      });
    }, sectionRef);

    return () => ctx.revert();
  }, [imagePosition]);

  const circlePosition = imagePosition === 'left' 
    ? 'left-[6vw]' 
    : 'right-[-10vw]';
  
  const textPosition = imagePosition === 'left'
    ? 'left-[62vw]'
    : 'left-[6vw]';

  return (
    <section 
      id={id}
      ref={sectionRef} 
      className="section-pinned bg-warm-white"
    >
      <div 
        ref={circleRef}
        className={`absolute top-[12vh] w-[76vw] h-[76vw] circle-image ${circlePosition}`}
      >
        <img src={image} alt={headline} />
      </div>
      
      <div 
        ref={textRef}
        className={`absolute ${textPosition} top-[30vh] w-[32vw]`}
      >
        <span className="font-mono-label text-text-secondary block mb-6">{label}</span>
        <h2 className="text-section font-display text-near-black mb-6">{headline}</h2>
        <p className="text-body text-text-secondary mb-8">{body}</p>
        <button className="text-near-black font-medium underline underline-offset-4 hover:text-accent transition-colors flex items-center gap-2">
          {cta}
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </section>
  );
}

// Testimonial Section
function TestimonialSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const circleRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      ScrollTrigger.create({
        trigger: sectionRef.current,
        start: 'top top',
        end: '+=130%',
        pin: true,
        scrub: 0.6,
        onUpdate: (self) => {
          const progress = self.progress;
          
          if (progress <= 0.3) {
            const enterProgress = progress / 0.3;
            gsap.set(circleRef.current, {
              scale: 0.7 + 0.3 * enterProgress,
              y: 10 * (1 - enterProgress) + 'vh',
              opacity: enterProgress
            });
            gsap.set(textRef.current, {
              x: 40 * (1 - enterProgress) + 'vw',
              opacity: enterProgress
            });
          }
          else if (progress <= 0.7) {
            gsap.set(circleRef.current, { scale: 1, y: 0, opacity: 1 });
            gsap.set(textRef.current, { x: 0, opacity: 1 });
          }
          else {
            const exitProgress = (progress - 0.7) / 0.3;
            gsap.set(circleRef.current, {
              scale: 1 + 0.08 * exitProgress,
              opacity: 1 - exitProgress * 0.65
            });
            gsap.set(textRef.current, {
              x: 18 * exitProgress + 'vw',
              opacity: 1 - exitProgress * 0.75
            });
          }
        }
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section 
      ref={sectionRef} 
      className="section-pinned bg-warm-white"
    >
      <div 
        ref={circleRef}
        className="absolute left-[6vw] top-[14vh] w-[62vw] h-[62vw] circle-image"
      >
        <img src="/testimonial_circle.jpg" alt="Khách hàng" />
      </div>
      
      <div 
        ref={textRef}
        className="absolute left-[62vw] top-[28vh] w-[32vw]"
      >
        <span className="font-mono-label text-text-secondary block mb-6">05 / CẢM NHẬN</span>
        <h2 className="text-section font-display text-near-black mb-8">KHÁCH HÀNG<br />NÓI GÌ</h2>
        <div className="relative">
          <span className="absolute -left-8 -top-4 text-[120px] leading-none text-near-black/5 font-serif">"</span>
          <p className="text-lg text-near-black italic mb-6 relative z-10">
            "Tôi thích cách đội ngũ lắng nghe—mỗi lần đến đều cảm thấy được chăm sóc thực sự."
          </p>
        </div>
        <p className="text-body text-text-secondary mb-6">— Minh An, Hội viên Cao cấp</p>
        <button className="text-near-black font-medium underline underline-offset-4 hover:text-accent transition-colors flex items-center gap-2">
          Đọc thêm cảm nhận
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </section>
  );
}

// FAQ Section
function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const sectionRef = useRef<HTMLDivElement>(null);

  const faqs = [
    {
      q: "Tôi có thể đặt lịch cho ngưởi thân không?",
      a: "Có, bạn có thể đặt lịch cho ngưởi thân. Chỉ cần cung cấp thông tin của họ khi đặt lịch hoặc liên hệ hotline để được hỗ trợ."
    },
    {
      q: "Làm sao để hủy hoặc đổi lịch hẹn?",
      a: "Bạn có thể hủy hoặc đổi lịch hẹn qua ứng dụng hoặc gọi điện trước 24 giờ. Lịch hẹn sẽ được chuyển sang thờ gian phù hợp."
    },
    {
      q: "Gói Cao cấp có thờ hạn không?",
      a: "Gói Cao cấp có thờ hạn 12 tháng kể từ ngày kích hoạt. Bạn có thể gia hạn bất kỳ lúc nào để tiếp tục tận hưởng quyền lợi."
    },
    {
      q: "Chính sách hoàn tiền như thế nào?",
      a: "Chúng tôi cam kết hoàn tiền 100% nếu bạn không hài lòng với dịch vụ. Vui lòng liên hệ trong vòng 7 ngày sau khi sử dụng dịch vụ."
    },
    {
      q: "Ứng dụng có tích điểm không?",
      a: "Có, mỗi lần sử dụng dịch vụ bạn sẽ được tích điểm. Điểm có thể đổi lấy dịch vụ hoặc voucher giảm giá."
    },
    {
      q: "Làm sao để trở thành CTV?",
      a: "Đăng ký tài khoản CTV trên website, sau đó đợi xét duyệt. Một khi được phê duyệt, bạn có thể giới thiệu khách hàng và nhận hoa hồng."
    }
  ];

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from('.faq-title', {
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 80%',
        },
        y: 24,
        opacity: 0,
        duration: 0.6
      });

      gsap.from('.faq-item', {
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 70%',
        },
        y: 20,
        opacity: 0,
        duration: 0.5,
        stagger: 0.1
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section 
      ref={sectionRef}
      className="bg-warm-white py-24 px-6 lg:px-12"
    >
      <div className="max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12">
          <div className="faq-title lg:sticky lg:top-24 lg:self-start">
            <span className="font-mono-label text-text-secondary block mb-4">10 / FAQ</span>
            <h2 className="text-section font-display text-near-black mb-4">CÂU HỎI<br />THƯỜNG GẶP</h2>
            <p className="text-body text-text-secondary">
              Giải đáp nhanh về đặt lịch, hủy lịch và quyền lợi hội viên.
            </p>
          </div>
          
          <div className="space-y-4">
            {faqs.map((faq, i) => (
              <div 
                key={i} 
                className="faq-item border-b border-near-black/10 pb-4"
              >
                <button
                  onClick={() => setOpenIndex(openIndex === i ? null : i)}
                  className="w-full flex items-center justify-between py-4 text-left"
                >
                  <span className="font-medium text-near-black pr-4">{faq.q}</span>
                  {openIndex === i ? (
                    <ChevronUp className="w-5 h-5 text-accent flex-shrink-0" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-text-secondary flex-shrink-0" />
                  )}
                </button>
                <div 
                  className={`overflow-hidden transition-all duration-300 ${
                    openIndex === i ? 'max-h-40 opacity-100' : 'max-h-0 opacity-0'
                  }`}
                >
                  <p className="text-body text-text-secondary pb-4">{faq.a}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// Contact Section
function ContactSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    message: ''
  });
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from('.contact-content', {
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 80%',
        },
        y: 24,
        opacity: 0,
        duration: 0.6
      });

      gsap.from('.contact-form', {
        scrollTrigger: {
          trigger: sectionRef.current,
          start: 'top 70%',
        },
        y: 32,
        opacity: 0,
        scale: 0.98,
        duration: 0.6
      });
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 3000);
  };

  return (
    <section 
      id="contact"
      ref={sectionRef}
      className="bg-near-black py-24 px-6 lg:px-12"
    >
      <div className="max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12">
          <div className="contact-content">
            <span className="font-mono-label text-white/50 block mb-4">11 / LIÊN HỆ</span>
            <h2 className="text-section font-display text-white mb-6">LIÊN HỆ</h2>
            <p className="text-body text-white/70 mb-8">
              Bạn cần tư vấn? Gửi tin nhắn và chúng tôi sẽ phản hồi trong 24 giờ.
            </p>
            
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <Phone className="w-5 h-5 text-accent" />
                <span className="text-white">1900 1234</span>
              </div>
              <div className="flex items-center gap-4">
                <Calendar className="w-5 h-5 text-accent" />
                <span className="text-white">Mon - Sun: 9:00 - 21:00</span>
              </div>
              <div className="flex items-center gap-4">
                <Heart className="w-5 h-5 text-accent" />
                <span className="text-white">info@tamgroup.vn</span>
              </div>
            </div>
          </div>
          
          <div className="contact-form bg-white/5 rounded-3xl p-8 border border-white/10">
            {submitted ? (
              <div className="h-full flex flex-col items-center justify-center text-center">
                <CheckCircle2 className="w-16 h-16 text-accent mb-4" />
                <h3 className="text-xl font-display text-white mb-2">ĐÃ GỬI!</h3>
                <p className="text-white/70">Chúng tôi sẽ liên hệ với bạn sớm.</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-white/70 text-sm mb-2">Họ tên</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder:text-white/30 focus:outline-none focus:border-accent"
                    placeholder="Nguyễn Văn A"
                    required
                  />
                </div>
                <div>
                  <label className="block text-white/70 text-sm mb-2">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder:text-white/30 focus:outline-none focus:border-accent"
                    placeholder="email@example.com"
                    required
                  />
                </div>
                <div>
                  <label className="block text-white/70 text-sm mb-2">Số điện thoại</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder:text-white/30 focus:outline-none focus:border-accent"
                    placeholder="090 123 4567"
                    required
                  />
                </div>
                <div>
                  <label className="block text-white/70 text-sm mb-2">Nội dung</label>
                  <textarea
                    value={formData.message}
                    onChange={(e) => setFormData({...formData, message: e.target.value})}
                    className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder:text-white/30 focus:outline-none focus:border-accent h-32 resize-none"
                    placeholder="Tôi muốn tư vấn về..."
                    required
                  />
                </div>
                <button type="submit" className="btn-primary w-full">
                  Gửi tin nhắn
                </button>
              </form>
            )}
          </div>
        </div>
        
        <div className="mt-16 pt-8 border-t border-white/10 text-center">
          <p className="text-white/50 text-sm">
            © Tam Group. Bảo mật thông tin khách hàng.
          </p>
        </div>
      </div>
    </section>
  );
}

// CTV Portal Modal
function CTVPortalModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [phone, setPhone] = useState('');
  const [checking, setChecking] = useState(false);
  const [result, setResult] = useState<null | { exists: boolean; message: string }>(null);

  const handleCheck = () => {
    if (!phone) return;
    setChecking(true);
    setTimeout(() => {
      setChecking(false);
      setResult({
        exists: Math.random() > 0.5,
        message: Math.random() > 0.5 
          ? 'Số điện thoại chưa có trong hệ thống. Bạn có thể giới thiệu khách hàng này!'
          : 'Số điện thoại đã tồn tại trong hệ thống.'
      });
    }, 1000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[70] bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-warm-white rounded-3xl p-8 max-w-md w-full">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-display text-near-black">CTV Portal</h3>
          <button onClick={onClose}>
            <X className="w-6 h-6 text-near-black" />
          </button>
        </div>
        
        <div className="mb-6">
          <label className="block text-near-black text-sm mb-2">Nhập SĐT cần kiểm tra</label>
          <div className="flex gap-2">
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="flex-1 bg-white border border-near-black/20 rounded-xl px-4 py-3 text-near-black focus:outline-none focus:border-accent"
              placeholder="090 123 4567"
            />
            <button 
              onClick={handleCheck}
              disabled={checking || !phone}
              className="btn-primary px-4 disabled:opacity-50"
            >
              {checking ? '...' : 'Kiểm tra'}
            </button>
          </div>
        </div>
        
        {result && (
          <div className={`p-4 rounded-xl mb-6 ${result.exists ? 'bg-red-100' : 'bg-green-100'}`}>
            <p className={result.exists ? 'text-red-700' : 'text-green-700'}>
              {result.message}
            </p>
          </div>
        )}
        
        <button className="btn-primary w-full">
          <Users className="w-5 h-5 mr-2" />
          Giới thiệu khách
        </button>
      </div>
    </div>
  );
}

// Main App
function App() {
  const [showIntro, setShowIntro] = useState(true);
  const [showCTVModal, setShowCTVModal] = useState(false);
  const mainRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize scroll snap after intro
    if (!showIntro) {
      const timer = setTimeout(() => {
        ScrollTrigger.refresh();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [showIntro]);

  return (
    <>
      {showIntro && <IntroAnimation onComplete={() => setShowIntro(false)} />}
      
      <div ref={mainRef} className={`transition-opacity duration-500 ${showIntro ? 'opacity-0' : 'opacity-100'}`}>
        <Navigation />
        
        <main className="relative">
          <HeroSection />
          <MembershipSection />
          <FeatureSection 
            label="02 / TRẢI NGHIỆM"
            headline="KHÔNG GIAN THƯ GIÃN"
            body="Ánh sáng dịu nhẹ, âm nhạc êm ái và liệu trình được cá nhân hóa—mỗi lần đến là một lần tái tạo năng lượng."
            cta="Xem không gian"
            image="/feature_relax_circle.jpg"
            imagePosition="left"
          />
          <FeatureSection 
            label="03 / ĐẶC QUYỀN"
            headline="DỊCH VỤ TẬN TÂM"
            body="Chuyên gia của chúng tôi lắng nghe, tư vấn và đồng hành cùng bạn trong từng bước—từ làn da đến phong cách."
            cta="Gặp chuyên gia"
            image="/feature_service_circle.jpg"
            imagePosition="right"
          />
          <FeatureSection 
            id="booking"
            label="04 / ĐẶT LỊCH"
            headline="LỊCH HẸN THÔNG MINH"
            body="Chọn dịch vụ, chuyên gia và khung giờ phù hợp—xác nhận tức thì, nhắc lịch tự động."
            cta="Đặt lịch ngay"
            image="/booking_circle.jpg"
            imagePosition="left"
          />
          <TestimonialSection />
          <FeatureSection 
            label="06 / QUYỀN LỢI"
            headline="ƯU ĐÃI HẤP DẪN"
            body="Giảm giá dịch vụ, ưu tiên lịch hẹn cuối tuần và quà tặng sinh nhật—chỉ dành cho hội viên."
            cta="Xem bảng quyền lợi"
            image="/benefits_circle.jpg"
            imagePosition="right"
          />
          <FeatureSection 
            label="07 / ĐỐI TÁC"
            headline="THƯƠNG HIỆU ĐỒNG HÀNH"
            body="Chúng tôi hợp tác với các thương hiệu chăm sóc da và tóc uy tín để mang lại kết quả rõ rệt."
            cta="Khám phá đối tác"
            image="/partners_circle.jpg"
            imagePosition="left"
          />
          <FeatureSection 
            label="08 / CÂU CHUYỆN"
            headline="BẮT ĐẦU HÀNH TRÌNH"
            body="Một lịch hẹn nhỏ có thể thay đổi cách bạn cảm nhận về bản thân. Hãy để chúng tôi đồng hành cùng bạn."
            cta="Tạo lịch hẹn đầu tiên"
            image="/story_circle.jpg"
            imagePosition="right"
          />
          <FeatureSection 
            label="09 / ỨNG DỤNG"
            headline="QUẢN LÝ MỌI LÚC"
            body="Theo dõi lịch hẹn, điểm thưởng và ưu đãi chỉ với vài chạm—trên iOS và Android."
            cta="Tải ứng dụng"
            image="/app_circle.jpg"
            imagePosition="left"
          />
          <FAQSection />
          <ContactSection />
        </main>
        
        <CTVPortalModal isOpen={showCTVModal} onClose={() => setShowCTVModal(false)} />
        
        {/* Floating CTV Button */}
        <button 
          onClick={() => setShowCTVModal(true)}
          className="fixed bottom-6 right-6 z-40 bg-near-black text-white px-6 py-3 rounded-full shadow-lg hover:bg-accent transition-colors flex items-center gap-2"
        >
          <Users className="w-5 h-5" />
          <span className="hidden sm:inline">CTV Portal</span>
        </button>
        
        {/* Grain Overlay */}
        <div className="grain-overlay" />
      </div>
    </>
  );
}

export default App;
