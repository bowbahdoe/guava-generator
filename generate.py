import os
import re

# os.system("rm -r guava-source")
# 36942e30fae35ff9cfca73b68bb3312b188bf01e
modules = [
    "base",
    "primitives",
    "escape",
    "math",
    "collect",
    "xml",
    "html",
    "graph",
    "hash",
    "io",
    "net",
    "reflect",
    "concurrent"
]

def process_LittleEndianByteArray(contents):
    using_unsafe_method = """  /**
   * Indicates that the loading of Unsafe was successful and the load and store operations will be
   * very efficient. May be useful for calling code to fall back on an alternative implementation
   * that is slower than Unsafe.get/store but faster than the pure-Java mask-and-shift.
   */
  static boolean usingUnsafe() {
    return (byteArray instanceof UnsafeByteArray);
  }"""
    if using_unsafe_method not in contents:
        raise Exception("LittleEndianByteArray: usingUnsafe() changed in some way")

    using_unsafe_safe_method = """  static boolean usingUnsafe() {
    return false;
  }"""
    contents = contents.replace(using_unsafe_method, using_unsafe_safe_method)

    unsafe_impl = """  /**
   * The only reference to Unsafe is in this nested class. We set things up so that if
   * Unsafe.theUnsafe is inaccessible, the attempt to load the nested class fails, and the outer
   * class's static initializer can fall back on a non-Unsafe version.
   */
  private enum UnsafeByteArray implements LittleEndianBytes {
    // Do *not* change the order of these constants!
    UNSAFE_LITTLE_ENDIAN {
      @Override
      public long getLongLittleEndian(byte[] array, int offset) {
        return theUnsafe.getLong(array, (long) offset + BYTE_ARRAY_BASE_OFFSET);
      }

      @Override
      public void putLongLittleEndian(byte[] array, int offset, long value) {
        theUnsafe.putLong(array, (long) offset + BYTE_ARRAY_BASE_OFFSET, value);
      }
    },
    UNSAFE_BIG_ENDIAN {
      @Override
      public long getLongLittleEndian(byte[] array, int offset) {
        long bigEndian = theUnsafe.getLong(array, (long) offset + BYTE_ARRAY_BASE_OFFSET);
        // The hardware is big-endian, so we need to reverse the order of the bytes.
        return Long.reverseBytes(bigEndian);
      }

      @Override
      public void putLongLittleEndian(byte[] array, int offset, long value) {
        // Reverse the order of the bytes before storing, since we're on big-endian hardware.
        long littleEndianValue = Long.reverseBytes(value);
        theUnsafe.putLong(array, (long) offset + BYTE_ARRAY_BASE_OFFSET, littleEndianValue);
      }
    };

    // Provides load and store operations that use native instructions to get better performance.
    private static final Unsafe theUnsafe;

    // The offset to the first element in a byte array.
    private static final int BYTE_ARRAY_BASE_OFFSET;

    /**
     * Returns an Unsafe. Suitable for use in a 3rd party package. Replace with a simple call to
     * Unsafe.getUnsafe when integrating into a JDK.
     *
     * @return an Unsafe instance if successful
     */
    @SuppressWarnings("removal") // b/318391980
    private static Unsafe getUnsafe() {
      try {
        return Unsafe.getUnsafe();
      } catch (SecurityException tryReflectionInstead) {
        // We'll try reflection instead.
      }
      try {
        return AccessController.doPrivileged(
            (PrivilegedExceptionAction<Unsafe>)
                () -> {
                  Class<Unsafe> k = Unsafe.class;
                  for (Field f : k.getDeclaredFields()) {
                    f.setAccessible(true);
                    Object x = f.get(null);
                    if (k.isInstance(x)) {
                      return k.cast(x);
                    }
                  }
                  throw new NoSuchFieldError("the Unsafe");
                });
      } catch (PrivilegedActionException e) {
        throw new RuntimeException("Could not initialize intrinsics", e.getCause());
      }
    }

    static {
      theUnsafe = getUnsafe();
      BYTE_ARRAY_BASE_OFFSET = theUnsafe.arrayBaseOffset(byte[].class);

      // sanity check - this should never fail
      if (theUnsafe.arrayIndexScale(byte[].class) != 1) {
        throw new AssertionError();
      }
    }
  }"""

    if unsafe_impl not in contents:
        raise Exception("LittleEndianByteArray: UnsafeByteArray changed somehow")

    contents = contents.replace(unsafe_impl, "")

    unsafe_init = """    try {
      /*
       * UnsafeByteArray uses Unsafe.getLong() in an unsupported way, which is known to cause
       * crashes on Android when running in 32-bit mode. For maximum safety, we shouldn't use
       * Unsafe.getLong() at all, but the performance benefit on x86_64 is too great to ignore, so
       * as a compromise, we enable the optimization only on platforms that we specifically know to
       * work.
       *
       * In the future, the use of Unsafe.getLong() should be replaced by ByteBuffer.getLong(),
       * which will have an efficient native implementation in JDK 9.
       *
       */
      String arch = System.getProperty("os.arch");
      if ("amd64".equals(arch) || "aarch64".equals(arch)) {
        theGetter =
            ByteOrder.nativeOrder().equals(ByteOrder.LITTLE_ENDIAN)
                ? UnsafeByteArray.UNSAFE_LITTLE_ENDIAN
                : UnsafeByteArray.UNSAFE_BIG_ENDIAN;
      }
    } catch (Throwable t) {
      // ensure we really catch *everything*
    }"""

    if unsafe_init not in contents:
        raise Exception("LittleEndianByteArray: Init code for unsafe array changed in some way")

    contents = contents.replace(unsafe_init, "")

    return contents

def process_AbstractFuture(contents):
    unsafe_atomic_helper = """  /**
   * {@link AtomicHelper} based on {@link sun.misc.Unsafe}.
   *
   * <p>Static initialization of this class will fail if the {@link sun.misc.Unsafe} object cannot
   * be accessed.
   */
  @SuppressWarnings({"sunapi", "removal"}) // b/318391980
  private static final class UnsafeAtomicHelper extends AtomicHelper {
    static final sun.misc.Unsafe UNSAFE;
    static final long LISTENERS_OFFSET;
    static final long WAITERS_OFFSET;
    static final long VALUE_OFFSET;
    static final long WAITER_THREAD_OFFSET;
    static final long WAITER_NEXT_OFFSET;

    static {
      sun.misc.Unsafe unsafe = null;
      try {
        unsafe = sun.misc.Unsafe.getUnsafe();
      } catch (SecurityException tryReflectionInstead) {
        try {
          unsafe =
              AccessController.doPrivileged(
                  new PrivilegedExceptionAction<sun.misc.Unsafe>() {
                    @Override
                    public sun.misc.Unsafe run() throws Exception {
                      Class<sun.misc.Unsafe> k = sun.misc.Unsafe.class;
                      for (java.lang.reflect.Field f : k.getDeclaredFields()) {
                        f.setAccessible(true);
                        Object x = f.get(null);
                        if (k.isInstance(x)) {
                          return k.cast(x);
                        }
                      }
                      throw new NoSuchFieldError("the Unsafe");
                    }
                  });
        } catch (PrivilegedActionException e) {
          throw new RuntimeException("Could not initialize intrinsics", e.getCause());
        }
      }
      try {
        Class<?> abstractFuture = AbstractFuture.class;
        WAITERS_OFFSET = unsafe.objectFieldOffset(abstractFuture.getDeclaredField("waiters"));
        LISTENERS_OFFSET = unsafe.objectFieldOffset(abstractFuture.getDeclaredField("listeners"));
        VALUE_OFFSET = unsafe.objectFieldOffset(abstractFuture.getDeclaredField("value"));
        WAITER_THREAD_OFFSET = unsafe.objectFieldOffset(Waiter.class.getDeclaredField("thread"));
        WAITER_NEXT_OFFSET = unsafe.objectFieldOffset(Waiter.class.getDeclaredField("next"));
        UNSAFE = unsafe;
      } catch (NoSuchFieldException e) {
        throw new RuntimeException(e);
      }
    }

    @Override
    void putThread(Waiter waiter, Thread newValue) {
      UNSAFE.putObject(waiter, WAITER_THREAD_OFFSET, newValue);
    }

    @Override
    void putNext(Waiter waiter, @CheckForNull Waiter newValue) {
      UNSAFE.putObject(waiter, WAITER_NEXT_OFFSET, newValue);
    }

    /** Performs a CAS operation on the {@link #waiters} field. */
    @Override
    boolean casWaiters(
        AbstractFuture<?> future, @CheckForNull Waiter expect, @CheckForNull Waiter update) {
      return UNSAFE.compareAndSwapObject(future, WAITERS_OFFSET, expect, update);
    }

    /** Performs a CAS operation on the {@link #listeners} field. */
    @Override
    boolean casListeners(AbstractFuture<?> future, @CheckForNull Listener expect, Listener update) {
      return UNSAFE.compareAndSwapObject(future, LISTENERS_OFFSET, expect, update);
    }

    /** Performs a GAS operation on the {@link #listeners} field. */
    @Override
    Listener gasListeners(AbstractFuture<?> future, Listener update) {
      return (Listener) UNSAFE.getAndSetObject(future, LISTENERS_OFFSET, update);
    }

    /** Performs a GAS operation on the {@link #waiters} field. */
    @Override
    Waiter gasWaiters(AbstractFuture<?> future, Waiter update) {
      return (Waiter) UNSAFE.getAndSetObject(future, WAITERS_OFFSET, update);
    }

    /** Performs a CAS operation on the {@link #value} field. */
    @Override
    boolean casValue(AbstractFuture<?> future, @CheckForNull Object expect, Object update) {
      return UNSAFE.compareAndSwapObject(future, VALUE_OFFSET, expect, update);
    }
  }"""

    if unsafe_atomic_helper not in contents:
        raise Exception("AbstractFuture: UnsafeAtomicHelper has changed in some way")

    contents = contents.replace(unsafe_atomic_helper, "")

    unsafe_atomic_helper_init = """  static {
    AtomicHelper helper;
    Throwable thrownUnsafeFailure = null;
    Throwable thrownAtomicReferenceFieldUpdaterFailure = null;

    try {
      helper = new UnsafeAtomicHelper();
    } catch (Exception | Error unsafeFailure) { // sneaky checked exception
      thrownUnsafeFailure = unsafeFailure;
      // catch absolutely everything and fall through to our 'SafeAtomicHelper'
      // The access control checks that ARFU does means the caller class has to be AbstractFuture
      // instead of SafeAtomicHelper, so we annoyingly define these here
      try {
        helper =
            new SafeAtomicHelper(
                newUpdater(Waiter.class, Thread.class, "thread"),
                newUpdater(Waiter.class, Waiter.class, "next"),
                newUpdater(AbstractFuture.class, Waiter.class, "waiters"),
                newUpdater(AbstractFuture.class, Listener.class, "listeners"),
                newUpdater(AbstractFuture.class, Object.class, "value"));
      } catch (Exception // sneaky checked exception
          | Error atomicReferenceFieldUpdaterFailure) {
        // Some Android 5.0.x Samsung devices have bugs in JDK reflection APIs that cause
        // getDeclaredField to throw a NoSuchFieldException when the field is definitely there.
        // For these users fallback to a suboptimal implementation, based on synchronized. This will
        // be a definite performance hit to those users.
        thrownAtomicReferenceFieldUpdaterFailure = atomicReferenceFieldUpdaterFailure;
        helper = new SynchronizedHelper();
      }
    }
    ATOMIC_HELPER = helper;

    // Prevent rare disastrous classloading in first call to LockSupport.park.
    // See: https://bugs.openjdk.java.net/browse/JDK-8074773
    @SuppressWarnings("unused")
    Class<?> ensureLoaded = LockSupport.class;

    // Log after all static init is finished; if an installed logger uses any Futures methods, it
    // shouldn't break in cases where reflection is missing/broken.
    if (thrownAtomicReferenceFieldUpdaterFailure != null) {
      log.get().log(Level.SEVERE, "UnsafeAtomicHelper is broken!", thrownUnsafeFailure);
      log.get()
          .log(
              Level.SEVERE,
              "SafeAtomicHelper is broken!",
              thrownAtomicReferenceFieldUpdaterFailure);
    }
  }
"""
    safe_atomic_helper_init = """  static {
    AtomicHelper helper;
    Throwable thrownAtomicReferenceFieldUpdaterFailure = null;

    try {
      helper =
              new SafeAtomicHelper(
                      newUpdater(Waiter.class, Thread.class, "thread"),
                      newUpdater(Waiter.class, Waiter.class, "next"),
                      newUpdater(AbstractFuture.class, Waiter.class, "waiters"),
                      newUpdater(AbstractFuture.class, Listener.class, "listeners"),
                      newUpdater(AbstractFuture.class, Object.class, "value"));
    } catch (RuntimeException | Error atomicReferenceFieldUpdaterFailure) {
      // Some Android 5.0.x Samsung devices have bugs in JDK reflection APIs that cause
      // getDeclaredField to throw a NoSuchFieldException when the field is definitely there.
      // For these users fallback to a suboptimal implementation, based on synchronized. This will
      // be a definite performance hit to those users.
      thrownAtomicReferenceFieldUpdaterFailure = atomicReferenceFieldUpdaterFailure;
      helper = new SynchronizedHelper();
    }
    ATOMIC_HELPER = helper;

    // Prevent rare disastrous classloading in first call to LockSupport.park.
    // See: https://bugs.openjdk.java.net/browse/JDK-8074773
    @SuppressWarnings("unused")
    Class<?> ensureLoaded = LockSupport.class;

    // Log after all static init is finished; if an installed logger uses any Futures methods, it
    // shouldn't break in cases where reflection is missing/broken.
    if (thrownAtomicReferenceFieldUpdaterFailure != null) {
      log.log(
          Level.ERROR, "SafeAtomicHelper is broken!", thrownAtomicReferenceFieldUpdaterFailure);
    }
  }"""

    if unsafe_atomic_helper_init not in contents:
        raise Exception("AbstractFuture: unsafe atomic helper init code changed in some way")

    contents = contents.replace(unsafe_atomic_helper_init, safe_atomic_helper_init)

    return contents

def process_UnsignedBytes(contents):
    unsafe_comparator_field = """    static final String UNSAFE_COMPARATOR_NAME =
        LexicographicalComparatorHolder.class.getName() + "$UnsafeComparator";\n"""
    
    if unsafe_comparator_field not in contents:
        raise Exception("UnsignedBytes: UNSAFE_COMPARATOR_NAME changed in some way")

    contents = contents.replace(unsafe_comparator_field, "")

    unsafe_comparator = """enum UnsafeComparator implements Comparator<byte[]> {
      INSTANCE;

      static final boolean BIG_ENDIAN = ByteOrder.nativeOrder().equals(ByteOrder.BIG_ENDIAN);

      /*
       * The following static final fields exist for performance reasons.
       *
       * In UnsignedBytesBenchmark, accessing the following objects via static final fields is the
       * fastest (more than twice as fast as the Java implementation, vs ~1.5x with non-final static
       * fields, on x86_32) under the Hotspot server compiler. The reason is obviously that the
       * non-final fields need to be reloaded inside the loop.
       *
       * And, no, defining (final or not) local variables out of the loop still isn't as good
       * because the null check on the theUnsafe object remains inside the loop and
       * BYTE_ARRAY_BASE_OFFSET doesn't get constant-folded.
       *
       * The compiler can treat static final fields as compile-time constants and can constant-fold
       * them while (final or not) local variables are run time values.
       */

      static final Unsafe theUnsafe = getUnsafe();

      /** The offset to the first element in a byte array. */
      static final int BYTE_ARRAY_BASE_OFFSET = theUnsafe.arrayBaseOffset(byte[].class);

      static {
        // fall back to the safer pure java implementation unless we're in
        // a 64-bit JVM with an 8-byte aligned field offset.
        if (!("64".equals(System.getProperty("sun.arch.data.model"))
            && (BYTE_ARRAY_BASE_OFFSET % 8) == 0
            // sanity check - this should never fail
            && theUnsafe.arrayIndexScale(byte[].class) == 1)) {
          throw new Error(); // force fallback to PureJavaComparator
        }
      }

      /**
       * Returns a sun.misc.Unsafe. Suitable for use in a 3rd party package. Replace with a simple
       * call to Unsafe.getUnsafe when integrating into a jdk.
       *
       * @return a sun.misc.Unsafe
       */
      @SuppressWarnings("removal") // b/318391980
      private static sun.misc.Unsafe getUnsafe() {
        try {
          return sun.misc.Unsafe.getUnsafe();
        } catch (SecurityException e) {
          // that's okay; try reflection instead
        }
        try {
          return java.security.AccessController.doPrivileged(
              new java.security.PrivilegedExceptionAction<sun.misc.Unsafe>() {
                @Override
                public sun.misc.Unsafe run() throws Exception {
                  Class<sun.misc.Unsafe> k = sun.misc.Unsafe.class;
                  for (java.lang.reflect.Field f : k.getDeclaredFields()) {
                    f.setAccessible(true);
                    Object x = f.get(null);
                    if (k.isInstance(x)) {
                      return k.cast(x);
                    }
                  }
                  throw new NoSuchFieldError("the Unsafe");
                }
              });
        } catch (java.security.PrivilegedActionException e) {
          throw new RuntimeException("Could not initialize intrinsics", e.getCause());
        }
      }

      @Override
      public int compare(byte[] left, byte[] right) {
        int stride = 8;
        int minLength = Math.min(left.length, right.length);
        int strideLimit = minLength & ~(stride - 1);
        int i;

        /*
         * Compare 8 bytes at a time. Benchmarking on x86 shows a stride of 8 bytes is no slower
         * than 4 bytes even on 32-bit. On the other hand, it is substantially faster on 64-bit.
         */
        for (i = 0; i < strideLimit; i += stride) {
          long lw = theUnsafe.getLong(left, BYTE_ARRAY_BASE_OFFSET + (long) i);
          long rw = theUnsafe.getLong(right, BYTE_ARRAY_BASE_OFFSET + (long) i);
          if (lw != rw) {
            if (BIG_ENDIAN) {
              return UnsignedLongs.compare(lw, rw);
            }

            /*
             * We want to compare only the first index where left[index] != right[index]. This
             * corresponds to the least significant nonzero byte in lw ^ rw, since lw and rw are
             * little-endian. Long.numberOfTrailingZeros(diff) tells us the least significant
             * nonzero bit, and zeroing out the first three bits of L.nTZ gives us the shift to get
             * that least significant nonzero byte.
             */
            int n = Long.numberOfTrailingZeros(lw ^ rw) & ~0x7;
            return ((int) ((lw >>> n) & UNSIGNED_MASK)) - ((int) ((rw >>> n) & UNSIGNED_MASK));
          }
        }

        // The epilogue to cover the last (minLength % stride) elements.
        for (; i < minLength; i++) {
          int result = UnsignedBytes.compare(left[i], right[i]);
          if (result != 0) {
            return result;
          }
        }
        return left.length - right.length;
      }

      @Override
      public String toString() {
        return "UnsignedBytes.lexicographicalComparator() (sun.misc.Unsafe version)";
      }
    }"""

    if unsafe_comparator not in contents:
        raise Exception("UnsignedBytes: Unsafe comparator changed in some way")

    contents = contents.replace(unsafe_comparator, "")

    best_comparator_function = """    /**
     * Returns the Unsafe-using Comparator, or falls back to the pure-Java implementation if unable
     * to do so.
     */
    static Comparator<byte[]> getBestComparator() {
      try {
        Class<?> theClass = Class.forName(UNSAFE_COMPARATOR_NAME);

        // requireNonNull is safe because the class is an enum.
        Object[] constants = requireNonNull(theClass.getEnumConstants());

        // yes, UnsafeComparator does implement Comparator<byte[]>
        @SuppressWarnings("unchecked")
        Comparator<byte[]> comparator = (Comparator<byte[]>) constants[0];
        return comparator;
      } catch (Throwable t) { // ensure we really catch *everything*
        return lexicographicalComparatorJavaImpl();
      }
    }"""

    if best_comparator_function not in contents:
        raise Exception("UnsignedBytes: getBestComparator changed in some way")

    bestest_comparator_function = """    /**
     * Returns the pure-Java implementation.
     */
    static Comparator<byte[]> getBestComparator() {
      return lexicographicalComparatorJavaImpl();
    }"""

    contents = contents.replace(best_comparator_function, bestest_comparator_function)
    return contents

def process_Striped64(contents):
    unsafe_code = """  /**
   * Returns a sun.misc.Unsafe. Suitable for use in a 3rd party package. Replace with a simple call
   * to Unsafe.getUnsafe when integrating into a jdk.
   *
   * @return a sun.misc.Unsafe
   */
  @SuppressWarnings("removal") // b/318391980
  private static sun.misc.Unsafe getUnsafe() {
    try {
      return sun.misc.Unsafe.getUnsafe();
    } catch (SecurityException tryReflectionInstead) {
    }
    try {
      return java.security.AccessController.doPrivileged(
          new java.security.PrivilegedExceptionAction<sun.misc.Unsafe>() {
            @Override
            public sun.misc.Unsafe run() throws Exception {
              Class<sun.misc.Unsafe> k = sun.misc.Unsafe.class;
              for (java.lang.reflect.Field f : k.getDeclaredFields()) {
                f.setAccessible(true);
                Object x = f.get(null);
                if (k.isInstance(x)) return k.cast(x);
              }
              throw new NoSuchFieldError("the Unsafe");
            }
          });
    } catch (java.security.PrivilegedActionException e) {
      throw new RuntimeException("Could not initialize intrinsics", e.getCause());
    }
  }"""

    if unsafe_code not in contents:
        raise Exception("Striped64: getUnsafe() changed in some way")

    contents = contents.replace(unsafe_code, "")

    unsafe_init = """  // Unsafe mechanics
  private static final sun.misc.Unsafe UNSAFE;
  private static final long baseOffset;
  private static final long busyOffset;

  static {
    try {
      UNSAFE = getUnsafe();
      Class<?> sk = Striped64.class;
      baseOffset = UNSAFE.objectFieldOffset(sk.getDeclaredField("base"));
      busyOffset = UNSAFE.objectFieldOffset(sk.getDeclaredField("busy"));
    } catch (Exception e) {
      throw new Error(e);
    }
  }"""

    varhandle_init = """  // Unsafe mechanics
  static final VarHandle baseOffset;
  static final VarHandle busyOffset;

  static {
    try {
      baseOffset = MethodHandles.lookup().
              in(Striped64.class).
              findVarHandle(Striped64.class, "base", long.class);

      busyOffset = MethodHandles.lookup().
              in(Striped64.class).
              findVarHandle(Striped64.class, "busy", int.class);
    } catch (Exception e) {
      throw new Error(e);
    }
  }"""

    if unsafe_init not in contents:
        raise Exception("Striped64: UNSAFE static init block changed in some way")

    contents = contents.replace(unsafe_init, varhandle_init)

    contents = contents.replace(
        "import java.util.Random;\n",
        """import java.lang.invoke.MethodHandles;
import java.lang.invoke.VarHandle;
import java.util.Random;\n""")


    unsafe_cas = """  /** CASes the base field. */
  final boolean casBase(long cmp, long val) {
    return UNSAFE.compareAndSwapLong(this, baseOffset, cmp, val);
  }

  /** CASes the busy field from 0 to 1 to acquire lock. */
  final boolean casBusy() {
    return UNSAFE.compareAndSwapInt(this, busyOffset, 0, 1);
  }"""

    safe_cas = """  /** CASes the base field. */
  final boolean casBase(long cmp, long val) {
    return baseOffset.compareAndSet(this, cmp, val);
  }

  /** CASes the busy field from 0 to 1 to acquire lock. */
  final boolean casBusy() {
    return busyOffset.compareAndSet(this, 0L, 1L);
  }"""

    if unsafe_cas not in contents:
        raise Exception("Striped64: casBusy() or casBase() changed somehow")

    contents = contents.replace(unsafe_cas, safe_cas)

    unsafe_cell = """  static final class Cell {
    volatile long p0, p1, p2, p3, p4, p5, p6;
    volatile long value;
    volatile long q0, q1, q2, q3, q4, q5, q6;

    Cell(long x) {
      value = x;
    }

    final boolean cas(long cmp, long val) {
      return UNSAFE.compareAndSwapLong(this, valueOffset, cmp, val);
    }

    // Unsafe mechanics
    private static final sun.misc.Unsafe UNSAFE;
    private static final long valueOffset;

    static {
      try {
        UNSAFE = getUnsafe();
        Class<?> ak = Cell.class;
        valueOffset = UNSAFE.objectFieldOffset(ak.getDeclaredField("value"));
      } catch (Exception e) {
        throw new Error(e);
      }
    }
  }"""

    safe_cell = """  static final class Cell {
    volatile long p0, p1, p2, p3, p4, p5, p6;
    volatile long value;
    volatile long q0, q1, q2, q3, q4, q5, q6;

    Cell(long x) {
      value = x;
    }

    final boolean cas(long cmp, long val) {
      return valueOffset.compareAndSet(this, cmp, val);
    }

    // Unsafe mechanics
    static final VarHandle valueOffset;

    static {
      try {
        valueOffset = MethodHandles.lookup().
                in(Cell.class).
                findVarHandle(Cell.class, "value", long.class);
      } catch (Exception e) {
        throw new Error(e);
      }
    }
  }"""

    if unsafe_cell not in contents:
        raise Exception("Striped64: Cell code changed in some way")

    contents = contents.replace(unsafe_cell, safe_cell)

    contents = contents.replace("""
import sun.misc.Unsafe;""", "")
    return contents


def process_contents(contents):
    for module in modules:
        if module == "concurrent":
            old_name = "com.google.common.util.concurrent"
        else:
            old_name = f"com.google.common.{module}"

        new_name = f"dev.mccue.guava.{module}"

        contents = contents.replace(old_name, new_name)
    contents = contents.replace("com.google.thirdparty", "dev.mccue.guava.net.thirdparty")

    contents = contents.replace("javax.annotation", "dev.mccue.jsr305")

    contents = contents.replace("java.util.logging.Logger.getLogger", "java.lang.System.getLogger")
    contents = contents.replace("java.util.logging.Logger", "java.lang.System.Logger")
    contents = contents.replace("java.util.logging.Level", "java.lang.System.Logger.Level")

    contents = contents.replace("Logger.getLogger", "System.getLogger")
    contents = contents.replace("log.info(", "log.log(java.lang.System.Logger.Level.INFO, ")
    contents = contents.replace("logger.info(", "logger.log(java.lang.System.Logger.Level.INFO, ")
    contents = contents.replace("logger.warning(", "logger.log(java.lang.System.Logger.Level.WARNING, ")
    contents = contents.replace("SEVERE", "ERROR")
    contents = contents.replace("FINEST", "DEBUG")
    contents = contents.replace("FINER", "TRACE")
    contents = contents.replace("FINE", "DEBUG")

    contents = re.sub(r'@\s*GwtCompatible\s*(\([^)]*\)|)', '', contents)
    contents = re.sub(r'@\s*GwtIncompatible\s*(\([^)]*\)|)', '', contents)
    contents = re.sub(r'@\s*J2ktIncompatible\s*(\([^)]*\)|)', '', contents)
    contents = re.sub(r'@\s*VisibleForTesting\s*(\([^)]*\)|)', '', contents)
    contents = re.sub(r'@\s*Beta\s*(\([^)]*\)|)', '', contents)
    contents = re.sub(r'@\s*J2ObjCIncompatible\s*(\([^)]*\)|)', '', contents)
    contents = re.sub(r'@\s*WeakOuter\s*(\([^)]*\)|)', '', contents)
    contents = re.sub(r'@\s*Weak\s*(\([^)]*\)|)', '', contents)
    contents = re.sub(r'@\s*RetainedWith\s*(\([^)]*\)|)', '', contents)
    contents = re.sub(r'@\s*ReflectionSupport\s*(\([^)]*\)|)', '', contents)

    contents = contents.replace(
        "\nimport com.google.common.annotations.GwtCompatible;",
        ""
    )
    contents = contents.replace(
        "\nimport com.google.common.annotations.GwtIncompatible;",
        ""
    )
    contents = contents.replace(
        "\nimport com.google.common.annotations.J2ktIncompatible;",
        ""
    )
    contents = contents.replace(
        "\nimport com.google.common.annotations.VisibleForTesting;",
        ""
    )

    contents = contents.replace(
        "\nimport com.google.common.annotations.Beta;",
        ""
    )
    contents = contents.replace(
        "\nimport com.google.j2objc.annotations.J2ObjCIncompatible;",
        ""
    )
    contents = contents.replace(
        "\nimport com.google.j2objc.annotations.WeakOuter;",
        ""
    )
    contents = contents.replace(
        "\nimport com.google.j2objc.annotations.Weak;",
        ""
    )
    contents = contents.replace(
        "\nimport com.google.j2objc.annotations.RetainedWith;",
        ""
    )
    contents = contents.replace(
        "\nimport com.google.j2objc.annotations.ReflectionSupport;",
        ""
    )

    contents = contents.replace(
        "\nimport sun.misc.Unsafe",
        ""
    )

    # Not perfect, since some of these we could keep as links
    contents = contents.replace(
      "{@linkplain",
      "{@code"
    )
    contents = contents.replace(
      "{@link",
      "{@code"
    )

    return contents

def process_ClosingFuture(contents):
    finalize = """  @SuppressWarnings("removal") // b/260137033
  @Override
  protected void finalize() {
    if (state.get().equals(OPEN)) {
      logger.get().log(SEVERE, "Uh oh! An open ClosingFuture has leaked and will close: {0}", this);
      FluentFuture<V> unused = finishToFuture();
    }
  }"""

    if finalize not in contents:
        raise Exception("ClosingFuture: Something changed about the finalize method")

    contents = contents.replace(finalize, "")

    return contents

def process_Types(contents):
    catch = """catch (AccessControlException e) {
            // OK: the method is accessible to us anyway. The setAccessible call is only for
            // unusual execution environments where that might not be true.
          }"""

    if catch not in contents:
        raise Exception("Types: access control changed in some way")

    new_catch = """catch (Exception e) {
            // OK: the method is accessible to us anyway. The setAccessible call is only for
            // unusual execution environments where that might not be true.
          }"""

    contents = contents.replace(catch, new_catch)

    return contents

def process_Throwables(contents):
    stack_trace_code = """  @J2ktIncompatible
  @GwtIncompatible // lazyStackTraceIsLazy, jlaStackTrace
  public static List<StackTraceElement> lazyStackTrace(Throwable throwable) {
    return lazyStackTraceIsLazy()
        ? jlaStackTrace(throwable)
        : unmodifiableList(asList(throwable.getStackTrace()));
  }

  /**
   * Returns whether {@link #lazyStackTrace} will use the special implementation described in its
   * documentation.
   *
   * @since 19.0
   * @deprecated This method always returns false on JDK versions past JDK 8 and on all Android
   *     versions.
   */
  @Deprecated
  @J2ktIncompatible
  @GwtIncompatible // getStackTraceElementMethod
  public static boolean lazyStackTraceIsLazy() {
    return getStackTraceElementMethod != null && getStackTraceDepthMethod != null;
  }

  @J2ktIncompatible
  @GwtIncompatible // invokeAccessibleNonThrowingMethod
  private static List<StackTraceElement> jlaStackTrace(Throwable t) {
    checkNotNull(t);
    /*
     * TODO(cpovirk): Consider optimizing iterator() to catch IOOBE instead of doing bounds checks.
     *
     * TODO(cpovirk): Consider the UnsignedBytes pattern if it performs faster and doesn't cause
     * AOSP grief.
     */
    return new AbstractList<StackTraceElement>() {
      /*
       * The following requireNonNull calls are safe because we use jlaStackTrace() only if
       * lazyStackTraceIsLazy() returns true.
       */
      @Override
      public StackTraceElement get(int n) {
        return (StackTraceElement)
            invokeAccessibleNonThrowingMethod(
                requireNonNull(getStackTraceElementMethod), requireNonNull(jla), t, n);
      }

      @Override
      public int size() {
        return (Integer)
            invokeAccessibleNonThrowingMethod(
                requireNonNull(getStackTraceDepthMethod), requireNonNull(jla), t);
      }
    };
  }

  @J2ktIncompatible
  @GwtIncompatible // java.lang.reflect
  private static Object invokeAccessibleNonThrowingMethod(
      Method method, Object receiver, Object... params) {
    try {
      return method.invoke(receiver, params);
    } catch (IllegalAccessException e) {
      throw new RuntimeException(e);
    } catch (InvocationTargetException e) {
      throw propagate(e.getCause());
    }
  }

  /** JavaLangAccess class name to load using reflection */
  @J2ktIncompatible @GwtIncompatible // not used by GWT emulation
  private static final String JAVA_LANG_ACCESS_CLASSNAME = "sun.misc.JavaLangAccess";

  /** SharedSecrets class name to load using reflection */
  @J2ktIncompatible
  @GwtIncompatible // not used by GWT emulation
  @VisibleForTesting
  static final String SHARED_SECRETS_CLASSNAME = "sun.misc.SharedSecrets";

  /** Access to some fancy internal JVM internals. */
  @J2ktIncompatible
  @GwtIncompatible // java.lang.reflect
  @CheckForNull
  private static final Object jla = getJLA();

  /**
   * The "getStackTraceElementMethod" method, only available on some JDKs so we use reflection to
   * find it when available. When this is null, use the slow way.
   */
  @J2ktIncompatible
  @GwtIncompatible // java.lang.reflect
  @CheckForNull
  private static final Method getStackTraceElementMethod = (jla == null) ? null : getGetMethod();

  /**
   * The "getStackTraceDepth" method, only available on some JDKs so we use reflection to find it
   * when available. When this is null, use the slow way.
   */
  @J2ktIncompatible
  @GwtIncompatible // java.lang.reflect
  @CheckForNull
  private static final Method getStackTraceDepthMethod = (jla == null) ? null : getSizeMethod(jla);

  /**
   * Returns the JavaLangAccess class that is present in all Sun JDKs. It is not allowed in
   * AppEngine, and not present in non-Sun JDKs.
   */
  @SuppressWarnings("removal") // b/318391980
  @J2ktIncompatible
  @GwtIncompatible // java.lang.reflect
  @CheckForNull
  private static Object getJLA() {
    try {
      /*
       * We load sun.misc.* classes using reflection since Android doesn't support these classes and
       * would result in compilation failure if we directly refer to these classes.
       */
      Class<?> sharedSecrets = Class.forName(SHARED_SECRETS_CLASSNAME, false, null);
      Method langAccess = sharedSecrets.getMethod("getJavaLangAccess");
      return langAccess.invoke(null);
    } catch (ThreadDeath death) {
      throw death;
    } catch (Throwable t) {
      /*
       * This is not one of AppEngine's allowed classes, so even in Sun JDKs, this can fail with
       * a NoClassDefFoundError. Other apps might deny access to sun.misc packages.
       */
      return null;
    }
  }

  /**
   * Returns the Method that can be used to resolve an individual StackTraceElement, or null if that
   * method cannot be found (it is only to be found in fairly recent JDKs).
   */
  @J2ktIncompatible
  @GwtIncompatible // java.lang.reflect
  @CheckForNull
  private static Method getGetMethod() {
    return getJlaMethod("getStackTraceElement", Throwable.class, int.class);
  }

  /**
   * Returns the Method that can be used to return the size of a stack, or null if that method
   * cannot be found (it is only to be found in fairly recent JDKs). Tries to test method {@link
   * sun.misc.JavaLangAccess#getStackTraceDepth(Throwable) getStackTraceDepth} prior to return it
   * (might fail some JDKs).
   *
   * <p>See <a href="https://github.com/google/guava/issues/2887">Throwables#lazyStackTrace throws
   * UnsupportedOperationException</a>.
   */
  @J2ktIncompatible
  @GwtIncompatible // java.lang.reflect
  @CheckForNull
  private static Method getSizeMethod(Object jla) {
    try {
      Method getStackTraceDepth = getJlaMethod("getStackTraceDepth", Throwable.class);
      if (getStackTraceDepth == null) {
        return null;
      }
      getStackTraceDepth.invoke(jla, new Throwable());
      return getStackTraceDepth;
    } catch (UnsupportedOperationException | IllegalAccessException | InvocationTargetException e) {
      return null;
    }
  }

  @SuppressWarnings("removal") // b/318391980
  @J2ktIncompatible
  @GwtIncompatible // java.lang.reflect
  @CheckForNull
  private static Method getJlaMethod(String name, Class<?>... parameterTypes) throws ThreadDeath {
    try {
      return Class.forName(JAVA_LANG_ACCESS_CLASSNAME, false, null).getMethod(name, parameterTypes);
    } catch (ThreadDeath death) {
      throw death;
    } catch (Throwable t) {
      /*
       * Either the JavaLangAccess class itself is not found, or the method is not supported on the
       * JVM.
       */
      return null;
    }
  }"""

    if stack_trace_code not in contents:
        raise Exception("Throwables: the code for getting JLA changed")

    new_stack_trace_code = """
  public static List<StackTraceElement> lazyStackTrace(Throwable throwable) {
    return unmodifiableList(asList(throwable.getStackTrace()));
  }

  /**
   * Returns whether {@link #lazyStackTrace} will use the special implementation described in its
   * documentation.
   *
   * @since 19.0
   * @deprecated This method always returns false on JDK versions past JDK 8 and on all Android
   *     versions.
   */
  @Deprecated
  public static boolean lazyStackTraceIsLazy() {
    return false;
  }"""

    contents = contents.replace(stack_trace_code, new_stack_trace_code)

    return contents

def process_FileBackedOutputStream(contents):
    finalize_constructor = """  public FileBackedOutputStream(int fileThreshold, boolean resetOnFinalize) {
    checkArgument(
        fileThreshold >= 0, "fileThreshold must be non-negative, but was %s", fileThreshold);
    this.fileThreshold = fileThreshold;
    this.resetOnFinalize = resetOnFinalize;
    memory = new MemoryOutput();
    out = memory;

    if (resetOnFinalize) {
      source =
          new ByteSource() {
            @Override
            public InputStream openStream() throws IOException {
              return openInputStream();
            }

            @SuppressWarnings("removal") // b/260137033
            @Override
            protected void finalize() {
              try {
                reset();
              } catch (Throwable t) {
                t.printStackTrace(System.err);
              }
            }
          };
    } else {
      source =
          new ByteSource() {
            @Override
            public InputStream openStream() throws IOException {
              return openInputStream();
            }
          };
    }
  }"""
    if finalize_constructor not in contents:
        raise Exception("FileBackedOutputStream: FileBackedOutputStream constructor changed in some way")
    new_finalize_constructor = """  private FileBackedOutputStream(int fileThreshold, boolean resetOnFinalize) {
    checkArgument(
        fileThreshold >= 0, "fileThreshold must be non-negative, but was %s", fileThreshold);
    this.fileThreshold = fileThreshold;
    this.resetOnFinalize = resetOnFinalize;
    memory = new MemoryOutput();
    out = memory;

    if (resetOnFinalize) {
      source =
          new ByteSource() {
            @Override
            public InputStream openStream() throws IOException {
              return openInputStream();
            }
          };
    } else {
      source =
          new ByteSource() {
            @Override
            public InputStream openStream() throws IOException {
              return openInputStream();
            }
          };
    }
  }"""
    contents = contents.replace(finalize_constructor, new_finalize_constructor)


    return contents
    

for module in modules:
    os.system(f"rm -rf guava-{module}/src/dev || true")

# commit_hash = "36942e30fae35ff9cfca73b68bb3312b188bf01e"
commit_hash = input("Guava commit hash: ")

os.system(f"git clone https://github.com/google/guava guava-source")

working_dir = os.getcwd()
os.chdir(working_dir + f"/guava-source") 
os.system("git fetch")
os.system(f"git checkout {commit_hash}")
os.chdir(working_dir)

for module in modules:
    os.system(f"mkdir -p guava-{module}/src/main/java/dev/mccue/guava/{module}")
    if module == "concurrent":
        source_path = "util/concurrent"
    else:
        source_path = f"{module}"
    os.system(f"cp -r guava-source/guava/src/com/google/common/{source_path} guava-{module}/src/main/java/dev/mccue/guava")

os.system("cp -r guava-source/guava/src/com/google/thirdparty guava-net/src/main/java/dev/mccue/guava/net")
os.system("cp -r guava-source/futures/failureaccess/src/com/google/common/util/concurrent/internal guava-concurrent/src/main/java/dev/mccue/guava/concurrent")
os.system("rm guava-base/src/main/java/dev/mccue/guava/base/internal/Finalizer.java")
os.system("rm guava-base/src/main/java/dev/mccue/guava/base/FinalizablePhantomReference.java")
os.system("rm guava-base/src/main/java/dev/mccue/guava/base/FinalizableReference.java")
os.system("rm guava-base/src/main/java/dev/mccue/guava/base/FinalizableReferenceQueue.java")
os.system("rm guava-base/src/main/java/dev/mccue/guava/base/FinalizableSoftReference.java")
os.system("rm guava-base/src/main/java/dev/mccue/guava/base/FinalizableWeakReference.java")

for module in modules:
    for (root,dirs,files) in os.walk(f'./guava-{module}', topdown=True):
        for file in files:
            if file.endswith(".java"):
                with open(f"{root}/{file}", "r") as f:
                    contents = "".join([line for line in f])
                with open(f"{root}/{file}", "w") as f:
                    if file == "Striped64.java":
                        print("Processing Striped64")
                        contents = process_Striped64(contents)
                    if file == "UnsignedBytes.java":
                        print("Processing UnsignedBytes")
                        contents = process_UnsignedBytes(contents)
                    if file == "AbstractFuture.java":
                        print("Processing AbstractFuture")
                        contents = process_AbstractFuture(contents)
                    if file == "LittleEndianByteArray.java":
                        print("Processing LittleEndianByteArray")
                        contents = process_LittleEndianByteArray(contents)
                    if file == "ClosingFuture.java":
                        print("Processing ClosingFuture")
                        contents = process_ClosingFuture(contents)
                    if file == "Types.java":
                        print("Processing Types")
                        contents = process_Types(contents)
                    if file == "Throwables.java":
                        print("Processing Throwables")
                        contents = process_Throwables(contents)
                    if file == "FileBackedOutputStream.java":
                        print("Processing FileBackedOutputStream")
                        contents = process_FileBackedOutputStream(contents)

                    contents = process_contents(contents)
                    f.write(contents)

# "sed -i '.bak' 's/--/—/g' *.txt"