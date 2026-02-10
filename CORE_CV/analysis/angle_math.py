import numpy as np

'''
Given three points: P1, P2, P3

1. Create vectors:
   vector_a = P1 - P2
   vector_b = P3 - P2

2. Calculate dot product:
   dot = vector_a · vector_b
   
3. Calculate magnitudes:
   mag_a = |vector_a|
   mag_b = |vector_b|
   
4. Calculate cosine of angle:
   cos(θ) = dot / (mag_a * mag_b)
   
5. Get angle:
   θ = arccos(cos(θ))
   
6. Convert to degrees:
   angle_degrees = θ * (180 / π)
'''


def calculate_angle(p1, p2, p3):
    """
    Calculate the angle at p2 formed by p1-p2-p3
    
    Args:
        p1: Tuple of (x, y) for first point
        p2: Tuple of (x, y) for middle point (angle is calculated here)
        p3: Tuple of (x, y) for third point
    
    Returns:
        Angle in degrees (0-180)
    
    Example:
        # Calculate knee angle
        hip = (100, 50)
        knee = (100, 150)
        ankle = (100, 250)
        angle = calculate_angle(hip, knee, ankle)
        print(angle)  # Will be close to 180 for straight leg
    """
    # Convert points to numpy arrays for easier math
    p1 = np.array(p1, dtype=np.float64)
    p2 = np.array(p2, dtype=np.float64)
    p3 = np.array(p3, dtype=np.float64)
    
    # Create vectors from p2 to p1 and p2 to p3
    vector_a = p1 - p2
    vector_b = p3 - p2
    
    # Calculate the dot product
    dot_product = np.dot(vector_a, vector_b)
    
    # Calculate magnitudes (lengths) of vectors
    magnitude_a = np.linalg.norm(vector_a)
    magnitude_b = np.linalg.norm(vector_b)
    
    # Avoid division by zero
    # (This can happen if p1==p2 or p2==p3, which shouldn't happen but is good to check)
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    
    # Calculate cosine of angle
    cos_angle = dot_product / (magnitude_a * magnitude_b)
    
    # Ensure cos_angle is in valid range [-1, 1]
    # (Sometimes floating point errors can give -1.0000001 which breaks arccos)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    
    # Calculate angle in radians
    angle_radians = np.arccos(cos_angle)
    
    # Convert to degrees
    angle_degrees = np.degrees(angle_radians)
    
    return float(angle_degrees)

def get_distance(p1, p2):
    """
    Calculate Euclidean distance between two points
    
    Args:
        p1: (x, y) tuple
        p2: (x, y) tuple
    
    Returns:
        float: distance in pixels
    
    Example:
        >>> get_distance((0, 0), (3, 4))
        5.0
    """
    p1 = np.array(p1, dtype=np.float64)
    p2 = np.array(p2, dtype=np.float64)
    
    return float(np.linalg.norm(p1 - p2))


def normalize_angle(angle):
    """
    Normalize angle to 0-180 range
    
    Args:
        angle: angle in degrees
    
    Returns:
        float: normalized angle (0-180)
    """
    # Ensure angle is positive
    angle = abs(angle)
    
    # Normalize to 0-180
    if angle > 180:
        angle = 360 - angle
    
    return angle


def test_angle_calculation():
    """Test the angle function with known values"""
    
    print("=" * 60)
    print("TESTING ANGLE CALCULATION")
    print("=" * 60)
    
    # Test 1: Straight line (180 degrees)
    print("\nTest 1: Straight line")
    p1 = (0, 0)
    p2 = (50, 50)
    p3 = (100, 100)
    angle = calculate_angle(p1, p2, p3)
    print(f"  Points: {p1} - {p2} - {p3}")
    print(f"  Expected: ~180°")
    print(f"  Got: {angle:.1f}°")
    print(f"  {'✓ PASS' if 175 < angle < 185 else '✗ FAIL'}")
    
    # Test 2: Right angle (90 degrees)
    print("\nTest 2: Right angle")
    p1 = (0, 0)
    p2 = (0, 100)
    p3 = (100, 100)
    angle = calculate_angle(p1, p2, p3)
    print(f"  Points: {p1} - {p2} - {p3}")
    print(f"  Expected: ~90°")
    print(f"  Got: {angle:.1f}°")
    print(f"  {'✓ PASS' if 85 < angle < 95 else '✗ FAIL'}")
    
    # Test 3: Acute angle (45°)
    print("\nTest 3: Acute angle (45°)")
    p1 = (100, 0)    # Point to the RIGHT of P2
    p2 = (0, 0)      # Vertex (angle point)
    p3 = (100, 100)  # Point to the RIGHT-UP at 45° from horizontal
    angle = calculate_angle(p1, p2, p3)
    print(f"  Expected: 45°, Got: {angle:.1f}°")
    print(f"  {'✓ PASS' if 40 < angle < 50 else '✗ FAIL'}")
    
    # Test 4: Obtuse angle (135°)
    print("\nTest 4: Obtuse angle (135°)")
    p1 = (0, 0)       # Up-left
    p2 = (100, 100)   # Corner (ANGLE HERE)
    p3 = (200, 100)   # Right (same y as p2)
    angle = calculate_angle(p1, p2, p3)
    print(f"  Expected: 135°, Got: {angle:.1f}°")
    print(f"  {'✓ PASS' if 130 < angle < 140 else '✗ FAIL'}")
    
    # Test 5: Very small angle (~6°)
    print("\nTest 5: Nearly closed angle (~6°)")
    p1 = (100, 0)    # Point to the RIGHT of P2
    p2 = (0, 0)      # Vertex (angle point)
    p3 = (100, 10)  # Very shallow angle ~6°
    angle = calculate_angle(p1, p2, p3)
    print(f"  Points: {p1} - {p2} - {p3}")
    print(f"  Expected: ~6°")
    print(f"  Got: {angle:.1f}°")
    print(f"  {'✓ PASS' if 0 < angle < 10 else '✗ FAIL'}")
    
    # Test 6: Distance
    dist = get_distance((0, 0), (3, 4))
    print(f"Distance test: {dist:.1f} (expected: 5.0)")
    
    print("\n" + "=" * 60)
    print("If all tests pass, your angle function works correctly!")
    print("=" * 60)
    
    


if __name__ == "__main__":
    # Run tests when file is executed directly
    test_angle_calculation()