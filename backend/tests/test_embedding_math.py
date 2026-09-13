"""Similarity, projection and grouping, against answers that can be worked out by hand."""

import pytest

from app.embeddings.math import cosine, kmeans, near_duplicates, project_2d


def test_cosine_of_the_same_direction_is_one_and_of_a_right_angle_zero():
    assert cosine([1.0, 2.0], [2.0, 4.0]) == pytest.approx(1.0)
    assert cosine([1.0, 0.0], [0.0, 3.0]) == pytest.approx(0.0)


def test_a_zero_vector_is_refused_rather_than_scored():
    with pytest.raises(ValueError, match="no direction"):
        cosine([0.0, 0.0], [1.0, 0.0])


def test_points_on_a_line_project_onto_the_first_axis_in_order():
    vectors = [[float(i), 2.0 * i, 0.0] for i in range(6)]
    points = project_2d(vectors)
    xs = [x for x, _ in points]
    assert all(abs(y) < 1e-6 for _, y in points)
    assert xs == sorted(xs) or xs == sorted(xs, reverse=True)
    assert project_2d(vectors) == points  # seeded: the same answers draw the same map


def test_two_obvious_groups_are_found_whatever_their_scale():
    near_x = [[1.0, 0.05], [10.0, 0.2], [3.0, -0.1]]
    near_y = [[0.1, 1.0], [-0.2, 7.0], [0.05, 2.0]]
    groups = kmeans(near_x + near_y, k=2)
    assert len(set(groups[:3])) == 1 and len(set(groups[3:])) == 1
    assert groups[0] != groups[3]


def test_near_duplicates_find_only_the_pair_that_points_the_same_way():
    pairs = near_duplicates([[1.0, 0.0], [0.0, 1.0], [2.0, 0.01]], threshold=0.99)
    assert [(i, j) for i, j, _ in pairs] == [(0, 2)]
